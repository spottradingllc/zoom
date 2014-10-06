import logging
import json
import os.path
import platform
from datetime import datetime
from multiprocessing import Lock
from time import sleep

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NoNodeError, NodeExistsError
from kazoo.handlers.threading import SequentialThreadingHandler

from spot.zoom.agent.sentinel.action.factory import ActionFactory
from spot.zoom.common.constants import (
    ZK_CONN_STRING,
)
from spot.zoom.agent.sentinel.common.thread_safe_object import (
    ApplicationMode,
    ThreadSafeObject
)
from spot.zoom.common.types import (
    PlatformType,
    AlertActionType,
    ApplicationState
)
from spot.zoom.agent.sentinel.util.decorators import (
    connected,
    time_this,
    catch_exception,
    run_only_one
)
from spot.zoom.agent.sentinel.util.helpers import verify_attribute
from spot.zoom.agent.sentinel.common.work_manager import WorkManager
from spot.zoom.agent.sentinel.common.task import Task

if 'Linux' in platform.platform():
    from spot.zoom.agent.sentinel.client.process_client import ProcessClient
else:
    from spot.zoom.agent.sentinel.client.process_client \
        import WindowsProcessClient as ProcessClient


class Application(object):
    """
    Service object to represent an deployed service.
    """
    def __init__(self, config, settings, conn, queue, system, application_type):
        """
        :type config: dict (xml)
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        :type conn: multiprocessing.Connection
        :type queue: spot.zoom.agent.sentinel.common.unique_queue.UniqueQueue
        :type system: spot.zoom.common.types.PlatformType
        :type application_type: spot.zoom.common.types.ApplicationType
        """
        self.config = config
        self._settings = settings
        self.name = verify_attribute(self.config, 'id', none_allowed=False)
        self._log = logging.getLogger('sent.{0}.app'.format(self.name))
        # informational attributes
        self._host = platform.node().upper()
        self._system = system
        self._predicates = list()
        self._running = True  # used to manually stop the run loop
        self._prev_state = None
        self._actions = dict()  # created in _reset_watches on zk connect
        self._env = os.environ.get('EnvironmentToUse', 'Staging')

        # tool-like attributes
        self.listener_lock = Lock()
        self._action_queue = queue
        self._mode = ApplicationMode(ApplicationMode.MANUAL)
        self._state = ThreadSafeObject(ApplicationState.OK)
        self._start_allowed = ThreadSafeObject(False)  # allowed_instances
        self._trigger_time = None
        self._login_user = None
        self._run_check_mode = False

        self._allowed_instances = self._init_allowed_inst(self.config)
        self._paths = self._init_paths(self.config, settings, application_type)

        # clients
        if self._system == PlatformType.LINUX:
            self.zkclient = KazooClient(
                hosts=ZK_CONN_STRING,
                handler=SequentialThreadingHandler(),
                logger=logging.getLogger('kazoo.app.{0}'.format(self.name)))
        elif self._system == PlatformType.WINDOWS:
            self.zkclient = KazooClient(hosts=ZK_CONN_STRING,
                                        handler=SequentialThreadingHandler())

        self.zkclient.add_listener(self._zk_listener)
        self._proc_client = self._init_proc_client(self.config,
                                                   settings,
                                                   application_type)

        self._actions = self._init_actions(settings)
        self._work_manager = self._init_work_manager(self._action_queue, conn)

    def run(self):
        """
        - Start the zookeeper client
        - Check for already running instances. 
        - Start main loop, periodically checking whether the process has failed.
        """
        self.zkclient.start()
        self._check_allowed_instances()
        # make all action objects start processing predicates
        self._check_mode()
        self._log.info('Starting to process Actions.')
        map(lambda x: x.start(), self._actions.values())  # start actions

        while self._running:
            sleep(5)
            
        self.uninitialize()

    @catch_exception(NodeExistsError)
    @connected
    def register(self, event=None):
        """
        Add entry to the state tree
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        if not self.zkclient.exists(self._paths['zk_state_path'],
                                    watch=self.register):
            ready_action = self._actions.get('register', None)
            # check that predicates are all met
            if ready_action is not None and ready_action.ready:

                self._log.info('Registering %s in state tree.' % self.name)
                self.zkclient.create(self._paths['zk_state_path'],
                                     ephemeral=True,
                                     makepath=True)

                # resolve any pager duty alarms
                self._create_alert_node(AlertActionType.RESOLVE)

                self._state.set_value(ApplicationState.OK)
                self._update_agent_node_with_app_details()

    @catch_exception(NoNodeError)
    @connected
    def unregister(self):
        """Remove entry from state tree"""
        self._log.info('Un-registering %s from state tree.' % self.name)
        self.zkclient.delete(self._paths['zk_state_path'])

    @catch_exception(RuntimeError)
    def uninitialize(self):
        """
        Gracefully stop this Zookeeper session, then free any resentinels 
        held by the client.
        """
        self._log.info('Stopping Zookeeper client')
        self._work_manager.stop()
        map(lambda x: x.stop(), self._actions.values())  # stop actions
        self.zkclient.stop()
        self.zkclient.close()

    @time_this
    def start(self, **kwargs):
        """
        Start actual process
        :param kwargs: passed from spot.zoom.handlers.control_agent_handlers
        """

        if kwargs.get('reset', True):
            self._proc_client.reset_counters()
        if kwargs.get('pause', False):
            self.ignore()

        self._trigger_time = self._get_current_time()
        self._login_user = kwargs.get('login_user', 'Zoom')
        self._state.set_value(ApplicationState.STARTING)
        self._update_agent_node_with_app_details()

        result = self._proc_client.start()

        if self._run_check_mode:  # Reset to global mode if restart with dep
            self._check_mode()
            self._run_check_mode = False

        if result != 0:
            self._state.set_value(ApplicationState.ERROR)
            self._create_alert_node(AlertActionType.TRIGGER)
        else:
            self._state.set_value(ApplicationState.OK)

        self._update_agent_node_with_app_details()

        return result

    @time_this
    def stop(self, **kwargs):
        """
        Stop actual process
        :param kwargs: passed from spot.zoom.handlers.control_agent_handlers
        """

        if kwargs.get('reset', True):
            self._proc_client.reset_counters()
        if kwargs.get('pause', False):
            self.ignore()

        self._trigger_time = self._get_current_time()
        self._login_user = kwargs.get('login_user', 'Zoom')
        self._state.set_value(ApplicationState.STOPPING)
        self._update_agent_node_with_app_details()

        result = self._proc_client.stop(**kwargs)

        if result != 0 and kwargs.get('argument', 'false') == 'false':
            self._state.set_value(ApplicationState.ERROR)
        else:
            self._state.set_value(ApplicationState.OK)

        self._update_agent_node_with_app_details()

        return result

    def restart(self, **kwargs):
        """
        :param kwargs: passed from spot.zoom.handlers.control_agent_handlers
        """
        self.stop(**kwargs)
        self.unregister()   # to ensure stopped app is unregistered
        self.start(**kwargs)

    def dep_restart(self, **kwargs):
        self._run_check_mode = True  # only used in self.start()
        self._action_queue.append(Task('start_if_ready', pipe=False))

    def start_if_ready(self):
        start_action = self._actions.get('start', None)
        if start_action is not None and start_action.ready:
            self.start()
        else:
            self._action_queue.append(Task('react', pipe=False))

    @time_this
    @connected
    def ignore(self, **kwargs):
        """
        :param kwargs: passed from spot.zoom.handlers.control_agent_handlers
        """
        self._mode.set_value(ApplicationMode.MANUAL)
        self._log.info('Mode is now "{0}"'.format(self._mode))
        self._update_agent_node_with_app_details()
        return 0

    @time_this
    @connected
    def react(self, **kwargs):
        """
        :param kwargs: passed from spot.zoom.handlers.control_agent_handlers
        """
        self._mode.set_value(ApplicationMode.AUTO)
        self._log.info('Mode is now "{0}"'.format(self._mode))
        self._update_agent_node_with_app_details()
        return 0

    @time_this
    @connected
    def notify(self):
        """
        Send notification to zookeeper that a dependency has gone down.
        """
        self._state.set_value(ApplicationState.NOTIFY)
        self._update_agent_node_with_app_details()
        return 0

    def terminate(self):
        """Terminate child thread/process"""
        self._running = False   

    def _app_details(self):
        return {'name': self.name,
                'host': self._host,
                'platform': self._system,
                'mode': self._mode.value,
                'state': self._state.value,
                'trigger_time': self._trigger_time,
                'login_user': self._login_user}

    @connected
    def _update_agent_node_with_app_details(self, event=None):
        """
        Register app data with the agent in the state tree.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """

        current_data = self._app_details()

        if self.zkclient.exists(self._paths['zk_state_base'],
                                watch=self._update_agent_node_with_app_details):
            data, stat = self.zkclient.get(self._paths['zk_state_base'])

            try:
                agent_apps = json.loads(data)
            except ValueError:
                agent_apps = dict()

            # make sure data is the most recent
            if current_data != agent_apps:
                self.zkclient.set(self._paths['zk_state_base'],
                                  json.dumps(current_data))
                self._log.debug('Registering app data {0}'.format(current_data))

    def _init_paths(self, config, settings, atype):
        """
        :rtype: dict
        """
        paths = dict()
        registrationpath = verify_attribute(config, 'registrationpath',
                                            none_allowed=True)

        if registrationpath is not None:
            paths['zk_state_base'] = registrationpath
        else:
            paths['zk_state_base'] = \
                self._pathjoin(settings.get('ZK_STATE_PATH'), atype, self.name)

        paths['zk_state_path'] = \
            self._pathjoin(paths['zk_state_base'], self._host)
        paths['zk_config_path'] = \
            self._pathjoin(settings.get('ZK_CONFIG_PATH'), atype, self.name)
        paths['zk_agent_path'] = \
            self._pathjoin(settings.get('ZK_AGENT_STATE_PATH'), self._host)
        paths['graphite_type_metric'] = \
            self._get_graphite_type_metric(paths['zk_state_base'])

        return paths

    def _init_allowed_inst(self, config):
        """
        :rtype: int
        """
        allowed_instances = verify_attribute(config, 'allowed_instances',
                                             none_allowed=True, cast=int)

        if allowed_instances is None:
            self._log.info('Allowed instances not specified. Assuming 1')
            allowed_instances = 1

        return allowed_instances

    def _init_proc_client(self, config, settings, atype):
        """Create the process client."""
        command = verify_attribute(config, 'command', none_allowed=True)
        script = verify_attribute(config, 'script', none_allowed=True)
        restartmax = verify_attribute(config, 'restartmax', none_allowed=True,
                                      cast=int)
        restart_on_crash = verify_attribute(config, 'restartoncrash',
                                            none_allowed=True)
        
        if restartmax is None:
            self._log.info('Restartmax not specified. Assuming 3.')
            restartmax = 3

        return ProcessClient(name=self.name,
                             command=command,
                             script=script,
                             apptype=atype,
                             system=self._system,
                             restart_max=restartmax,
                             restart_on_crash=restart_on_crash,
                             graphite_app_metric=self._paths['graphite_type_metric'],
                             settings=settings
                             )

    def _init_actions(self, settings):
        """
        :rtype: dict
        """
        action_factory = ActionFactory(component=self,
                                       zkclient=self.zkclient,
                                       proc_client=self._proc_client,
                                       action_queue=self._action_queue,
                                       mode=self._mode,
                                       system=self._system,
                                       pred_list=self._predicates,
                                       settings=settings)
        return action_factory.create(self.config)

    def _init_work_manager(self, queue, pipe):
        """
        :rtype: spot.zoom.agent.sentinel.common.work_manager.WorkManager
        """
        acceptable_work = dict()
        for w in self._settings.get('ALLOWED_WORK'):
            if hasattr(self, w):
                acceptable_work[w] = self.__getattribute__(w)
            else:
                self._log.error('Class has no method {0}'.format(w))

        manager = WorkManager(self.name, queue, pipe, acceptable_work)
        manager.start()
        return manager

    @connected
    def _check_allowed_instances(self, event=None):
        """
        Check whether the allowed instances is less than current instance 
        count. Set watch on that node to see if it changes.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        try:
            children = self.zkclient.get_children(
                self._paths['zk_state_base'],
                watch=self._check_allowed_instances
            )
            num_of_children = len(children)
            if not(num_of_children < self._allowed_instances):
                self._log.info('Running instances of {0} ({1}) is >= allowed '
                               'instances ({2}).'
                               .format(self.name, num_of_children,
                                       self._allowed_instances))
                self._start_allowed.set_value(False)
 
            else:
                self._log.info('Running instances of {0} ({1}) is < '
                               'allowed instances ({2}). It should be allowed '
                               'to start.'.format(self.name, num_of_children,
                                                  self._allowed_instances))
                self._start_allowed.set_value(True)
        except NoNodeError:
            self._log.info('ZK path {0} does not exist. Assuming no instances'
                           ' are running.'.format(self._paths['zk_state_base']))

    @connected
    def _check_mode(self, event=None):
        """
        Check global run mode for the agents.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        modepath = self._pathjoin(self._settings.get('ZK_GLOBAL_PATH'), 'mode')
        try:
            data, stat = self.zkclient.get(modepath, watch=self._check_mode)
            j = json.loads(data)
            self._log.info('Getting mode from Zookeeper from path: {0}'.
                           format(modepath))
            self._mode.set_value(str(j.get(u'mode', ApplicationMode.MANUAL)))
            self._log.info('Setting mode to "{0}"'.format(self._mode))
            self._update_agent_node_with_app_details()
        except NoNodeError:
            self._log.info('ZK path {0} does not exist. Assuming mode "manual"'
                           .format(modepath))
        except Exception:
            self._log.exception('An uncaught exception has occurred.')

    def _pathjoin(self, *args):
        """
        Helper function to join paths. Uses string joining if it is a Windows
        box.
        :rtype: str
        """
        if self._system == PlatformType.LINUX:
            return os.path.join(*args)
        elif self._system == PlatformType.WINDOWS:
            return '/'.join(args)

    def _get_graphite_type_metric(self, state_path):
        # splits the state path at 'application' and returns the latter index
        type_path = state_path.split('state/', 1)[1]
        type_metric = type_path.replace('/', '.')
        return type_metric

    def _get_current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_alert_details(self):
        return {
            "action": None,
            "subdomain": self._settings.get("PAGERDUTY_SUBDOMAIN"),
            "org_token": self._settings.get("PAGERDUTY_API_TOKEN"),
            "svc_token": self._settings.get("PAGERDUTY_SERVICE_TOKEN"),
            "key": self._pathjoin('sentinel', self.name, self._host),
            "description": (
                'Sentinel Error: Application {0} has failed to start on host '
                '{1}.'.format(self.name, self._host)
            ),
            "details": (
                'Sentinel Error: Application {0} has failed to start on host '
                '{1}.\nReview the application log and contact the appropriate '
                'development group.'.format(self.name, self._host)
            )
        }

    @connected
    def _create_alert_node(self, alert_action):
        """
        Create Node in ZooKeeper that will result in a PagerDuty alarm
        :type alert_action: spot.zoom.common.types.AlertActionType
        """
        if self._env in self._settings.get('PAGERDUTY_ENABLED_ENVIRONMENTS'):
            self._log.info('Creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))
            alert_details = self._get_alert_details()
            alert_details['action'] = alert_action
            path = self._pathjoin(self._settings.get('ZK_ALERT_PATH'), 'alert')
            self.zkclient.create(path,
                                 value=json.dumps(alert_details),
                                 sequence=True)
        else:
            self._log.info('Not creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))

    @catch_exception(Exception, traceback=True)
    @run_only_one('listener_lock')
    def _reset_after_connection_loss(self):
        """
        Recreates all actions and predicates after connection loss.
        Recheck the mode and allowed instances.
        """
        if self._running:
            self._log.info('Application listener callback triggered')
            map(lambda x: x.stop(), self._actions.values())  # stop actions
            self._actions.clear()
            self._predicates = []
            self._actions = self._init_actions(self._settings)
            map(lambda x: x.reset(), self._predicates)  # reset predicates
            map(lambda x: x.start(), self._actions.values())  # start actions
            self._check_allowed_instances()
            self._check_mode()
            self._log.info('Application listener callback complete!')
        else:
            self._log.info('The daemon has called for termination. '
                           'Not trying to reset after connection loss.')

    def _zk_listener(self, state):
        """
        The callback function that runs when the connection state to Zookeeper
        changes.
        Either passes or immediately spawns a new thread that resets any
        watches, etc., so that it can listen to future connection state changes.
        """
        try:
            self._log.info('Zookeeper Connection went from {0} to {1}'
                           .format(self._prev_state, state))
            if self._prev_state is None and state == KazooState.CONNECTED:
                pass
            elif (self._prev_state == KazooState.LOST
                  and state == KazooState.CONNECTED):
                self.zkclient.handler.spawn(self._reset_after_connection_loss)
            elif (self._prev_state == KazooState.CONNECTED
                  and state == KazooState.SUSPENDED):
                pass
            elif (self._prev_state == KazooState.CONNECTED
                  and state == KazooState.LOST):
                pass
            elif (self._prev_state == KazooState.SUSPENDED
                  and state == KazooState.LOST):
                pass
            elif (self._prev_state == KazooState.SUSPENDED
                  and state == KazooState.CONNECTED):
                self.zkclient.handler.spawn(self._reset_after_connection_loss)
            elif state == KazooState.CONNECTED:
                self.zkclient.handler.spawn(self._reset_after_connection_loss)
            else:
                self._log.info('Zookeeper Connection in unknown state: {0}'
                               .format(state))
                return
            self._prev_state = state

        except Exception:
            self._log.exception('An uncaught exception has occurred')

    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return ("{0}(name={1}, runmode={2}, actions={3})"
                .format(self.__class__.__name__,
                        self.name,
                        self._mode,
                        self._actions.keys())
                )
