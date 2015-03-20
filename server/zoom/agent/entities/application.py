import logging
import json
import os.path
import platform
import re
import socket
from datetime import datetime
from multiprocessing import Lock
from time import sleep

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NoNodeError, NodeExistsError
from kazoo.handlers.threading import SequentialThreadingHandler

from zoom.agent.action.factory import ActionFactory
from zoom.common.constants import get_zk_conn_string
from zoom.agent.entities.thread_safe_object import (
    ApplicationMode,
    ThreadSafeObject
)
from zoom.common.types import (
    PlatformType,
    AlertActionType,
    AlertReason,
    ApplicationType,
    ApplicationState
)
from zoom.common.decorators import (
    connected,
    time_this,
    catch_exception,
    run_only_one
)
from zoom.agent.util.helpers import verify_attribute
from zoom.agent.entities.restart import RestartLogic
from zoom.agent.entities.work_manager import WorkManager
from zoom.agent.entities.task import Task

if 'Linux' in platform.platform():
    from zoom.agent.client.process_client import ProcessClient
else:
    from zoom.agent.client.process_client \
        import WindowsProcessClient as ProcessClient


class Application(object):
    """
    Service object to represent an deployed service.
    """
    def __init__(self, config, settings, conn, queue, system, application_type,
                 cancel_flag):
        """
        :type config: dict (xml)
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type conn: multiprocessing.Connection
        :type queue: zoom.agent.entities.unique_queue.UniqueQueue
        :type system: zoom.common.types.PlatformType
        :type application_type: zoom.common.types.ApplicationType
        :type cancel_flag: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        """
        self.config = config
        self._settings = settings
        self.name = verify_attribute(self.config, 'id', none_allowed=False)
        self._log = logging.getLogger('sent.{0}.app'.format(self.name))
        # informational attributes
        self._host = socket.getfqdn()
        self._system = system
        self._predicates = list()
        self._running = True  # used to manually stop the run loop
        self._prev_state = None
        self._actions = dict()  # created in _reset_watches on zk connect
        self._env = os.environ.get('EnvironmentToUse', 'Staging')
        self._apptype = application_type
        self._restart_on_crash = \
            verify_attribute(self.config, 'restart_on_crash', none_allowed=True)

        # tool-like attributes
        self.listener_lock = Lock()
        self._action_queue = queue
        self._mode = ApplicationMode(
            ApplicationMode.MANUAL,
            callback=self._update_agent_node_with_app_details)
        self._state = ThreadSafeObject(
            ApplicationState.OK,
            callback=self._update_agent_node_with_app_details)
        self._start_stop_time = ''  # Default to empty string for comparison
        self._login_user = 'Zoom'  # Default to Zoom
        self._user_set_in_react = False
        self._run_check_mode = False
        self._pd_svc_key = verify_attribute(config, 'pagerduty_service',
                                            none_allowed=True)
        self._read_only = False

        self._paths = self._init_paths(self.config, settings, application_type)

        # clients
        if self._system == PlatformType.LINUX:
            self.zkclient = KazooClient(
                hosts=get_zk_conn_string(),
                handler=SequentialThreadingHandler(),
                logger=logging.getLogger('kazoo.app.{0}'.format(self.name)))
        elif self._system == PlatformType.WINDOWS:
            self.zkclient = KazooClient(hosts=get_zk_conn_string(),
                                        handler=SequentialThreadingHandler())

        self.zkclient.add_listener(self._zk_listener)
        self._proc_client = self._init_proc_client(self.config,
                                                   settings,
                                                   application_type,
                                                   cancel_flag)

        self._actions = self._init_actions(settings)
        self._work_manager = self._init_work_manager(self._action_queue, conn)

    def app_details(self):
        return {'name': self.name,
                'host': self._host,
                'platform': self._system,
                'mode': self._mode.value,
                'state': self._state.value,
                'start_stop_time': self._start_stop_time,
                'login_user': self._login_user,
                'read_only': self._read_only}

    def run(self):
        """
        - Start the zookeeper client
        - Check for already running instances. 
        - Start main loop, periodically checking whether the process has failed.
        """
        self.zkclient.start()
        # make all action objects start processing predicates
        self._log.info('Starting to process Actions.')
        map(lambda x: x.start(), self._actions.values())  # start actions
        self._check_mode()  # get global mode AFTER starting actions

        while self._running:
            sleep(5)

        self.uninitialize()

    @catch_exception(NodeExistsError)
    @connected
    def register(self, **kwargs):
        """
        Add entry to the state tree
        """
        if not self.zkclient.exists(self._paths['zk_state_path']):
            if self._action_is_ready('register'):
                self._log.info('Registering %s in state tree.' % self.name)
                self.zkclient.create(self._paths['zk_state_path'],
                                     ephemeral=True,
                                     makepath=True)

                # resolve any pager duty alarms
                self._create_alert_node(AlertActionType.RESOLVE,
                                        AlertReason.RESOLVED)
                # reset restart counters, etc
                self._proc_client.reset_counters()

                self._state.set_value(ApplicationState.STARTED)

    @catch_exception(NoNodeError)
    @connected
    def unregister(self, **kwargs):
        """Remove entry from state tree"""
        if self._action_is_ready('unregister'):
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
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        # Restart from UI: ran_stop=True, stay_down=False
        # Stop from UI: ran_stop=True, stay_down=True
        # Crash: ran_stop=False, stay_down=False
        if self._proc_client.restart_logic.ran_stop \
                and self._proc_client.restart_logic.stay_down \
                and self._apptype == ApplicationType.APPLICATION:

            self._log.info('Not starting. App was stopped with Zoom.')
            return 0
        elif self._proc_client.restart_logic.crashed and \
                not self._restart_on_crash:
            self._log.info('Not starting. The application has crashed.')
            return 0
        else:
            self._log.debug('Start allowed.')

        if kwargs.get('reset', True):
            self._proc_client.reset_counters()
        if kwargs.get('pause', False):
            self.ignore()
        pd_enabled = kwargs.get('pd_enabled', True)

        self._start_stop_time = self._get_current_time()

        # set login user if not set in react
        if not self._user_set_in_react:
            self._login_user = kwargs.get('login_user', 'Zoom')
        self._state.set_value(ApplicationState.STARTING)

        result = self._proc_client.start()

        if self._run_check_mode:  # Reset to global mode if restart with dep
            self._check_mode()
            self._run_check_mode = False

        if result == 0:
            self._state.set_value(ApplicationState.STARTED)
        else:
            self._state.set_value(ApplicationState.ERROR)
            if pd_enabled:
                self._create_alert_node(AlertActionType.TRIGGER,
                                        AlertReason.FAILEDTOSTART)
            else:
                self._log.debug('PD is disabled, not sending alert.')

        return result

    @time_this
    def stop(self, **kwargs):
        """
        Stop actual process
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """

        if kwargs.get('reset', True):
            self._proc_client.reset_counters()
        if kwargs.get('pause', False):
            self.ignore()

        self._start_stop_time = self._get_current_time()
        self._login_user = kwargs.get('login_user', 'Zoom')
        self._state.set_value(ApplicationState.STOPPING)

        result = self._proc_client.stop(**kwargs)

        if result != 0 and kwargs.get('argument', 'false') == 'false':
            self._state.set_value(ApplicationState.ERROR, run_callback=False)
        else:
            self._state.set_value(ApplicationState.STOPPED, run_callback=False)

        sleep(5)  # give everything time to catch up, not sure why anymore...
        self._update_agent_node_with_app_details()

        # reset this value back to False
        self._user_set_in_react = False

        return result

    def restart(self, **kwargs):
        """
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        # if not self._action_is_ready('restart', allow_undefined=True):
        #     self._log.info('Restart action not ready.')
        #     return

        self._log.info('Running Restart. Queuing stop, unregister, start.')
        self._action_queue.clear()
        self._action_queue.append_unique(Task('stop', kwargs=kwargs))
        self._action_queue.append_unique(Task('unregister'))
        self._action_queue.append_unique(Task('start', kwargs=kwargs))

    def dep_restart(self, **kwargs):
        self._run_check_mode = True  # only used in self.start()
        self._action_queue.append(Task('start_if_ready', kwargs=kwargs, pipe=False))

    def start_if_ready(self, **kwargs):
        if self._action_is_ready('start'):
            self.start(**kwargs)
        # if start action doesn't exist, a.k.a. read only
        elif self._actions.get('start', None) is None:
            self.start(**kwargs)
        else:
            self._action_queue.append(Task('react', kwargs=kwargs, pipe=False))

    @time_this
    @connected
    def ignore(self, **kwargs):
        """
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        self._mode.set_value(ApplicationMode.MANUAL)
        self._log.info('Mode is now "{0}"'.format(self._mode))
        return 0

    @time_this
    @connected
    def react(self, **kwargs):
        """
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        self._mode.set_value(ApplicationMode.AUTO)
        self._log.info('Mode is now "{0}"'.format(self._mode))

        # when react is called through "restart with dependencies" command
        self._user_set_in_react = True
        self._login_user = kwargs.get('login_user', 'Zoom')
        return 0

    @time_this
    @connected
    def notify(self, **kwargs):
        """
        Send notification to zookeeper that a dependency has gone down.
        """
        # Application failed to start. Already sent PD alert
        if self._state == ApplicationState.ERROR:
            return

        pd_enabled = kwargs.get('pd_enabled', True)

        if not self._action_is_ready('notify'):
            self._log.info('notify action not defined or not ready.')
            return

        if not self._proc_client.restart_logic.ran_stop:
            # the application has crashed
            self._state.set_value(ApplicationState.NOTIFY)
            if pd_enabled:
                self._create_alert_node(AlertActionType.TRIGGER,
                                        AlertReason.CRASHED)
            else:
                self._log.debug('PD is disabled, not sending alert.')
        else:
            self._log.debug("Service shut down gracefully")

    def terminate(self):
        """Terminate child thread/process"""
        self._running = False   

    def _action_is_ready(self, action_name, allow_undefined=False):
        """
        Check if a configured action's predicates are met
        :type action_name: str
        :type allow_undefined: bool
        :rtype: bool
        """
        action = self._actions.get(action_name, None)
        if allow_undefined:
            if action is None:
                return True

        return action is not None and action.ready

    @connected
    def _update_agent_node_with_app_details(self, event=None):
        """
        Register app data with the agent in the state tree.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        if self._running and \
                not self.zkclient.exists(self._paths['zk_state_base']):
            self.zkclient.create(self._paths['zk_state_base'], makepath=True)

        data, stat = self.zkclient.get(self._paths['zk_state_base'])

        try:
            agent_apps = json.loads(data)
        except ValueError:
            agent_apps = dict()

        # check for config conflict
        other_host = agent_apps.get('host')
        if other_host is not None and self._host != other_host:
            self._log.error('There is a config conflict with {0}. Updates '
                            'will no longer be sent until it is resolved.'
                            .format(other_host))
            self._state.set_value(ApplicationState.CONFIG_ERROR,
                                  run_callback=False)

        # make sure data is the most recent
        if self.app_details() != agent_apps:
            self.zkclient.set(self._paths['zk_state_base'],
                              json.dumps(self.app_details()))
            self._log.debug('Registering app data {0}'
                            .format(self.app_details()))

        # set watch
        if self._state != ApplicationState.CONFIG_ERROR:
            self.zkclient.get(
                self._paths['zk_state_base'],
                watch=self._update_agent_node_with_app_details)
        else:
            self._log.error('Shutting down because of config error.')
            self.terminate()

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

        return paths

    def _init_proc_client(self, config, settings, atype, cancel_flag):
        """Create the process client."""
        command = verify_attribute(config, 'command', none_allowed=True)
        script = verify_attribute(config, 'script', none_allowed=True)
        restartmax = verify_attribute(config, 'restartmax', none_allowed=True,
                                      cast=int)

        if restartmax is None:
            self._log.info('Restartmax not specified. Assuming 3.')
            restartmax = 3

        g_names = self._get_graphite_metric_names()

        return ProcessClient(name=self.name,
                             command=command,
                             script=script,
                             apptype=atype,
                             system=self._system,
                             restart_logic=RestartLogic(restartmax),
                             graphite_metric_names=g_names,
                             settings=settings,
                             cancel_flag=cancel_flag)

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

        actions = action_factory.create(self.config)

        self._determine_read_only(actions)

        return actions

    def _determine_read_only(self, actions):
        start_action = actions.get('start', None)

        if start_action is None:
            self._read_only = True
        elif start_action.disabled is True:
            self._read_only = True
        else:
            self._read_only = False

    def _init_work_manager(self, queue, pipe):
        """
        :rtype: zoom.agent.entities.work_manager.WorkManager
        """
        acceptable_work = dict()
        # actions have additional logic, so use those if available
        for k, v in self._actions.iteritems():
            acceptable_work[k] = v.run

        # if action is not available, add public methods
        for attribute in [a for a in dir(self) if not a.startswith('_')]:
            obj = getattr(self, attribute)
            if hasattr(obj, '__call__'):
                if attribute not in acceptable_work:
                    acceptable_work[attribute] = obj
                else:
                    self._log.debug('Method {0} already assigned to action.'
                                    .format(attribute))

        manager = WorkManager(self.name, queue, pipe, acceptable_work)
        manager.start()
        return manager

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

    def _get_graphite_metric_names(self):
        """
        splits the state path at 'application' and returns the latter index
        :rtype: dict
        """
        type_path = self._paths.get('zk_state_base')\
            .split(self._settings.get('ZK_STATE_PATH') + '/', 1)[1]
        type_metric = type_path.replace('/', '.')
        result_path = self._settings.get('GRAPHITE_RESULT_METRIC')
        runtime_path = self._settings.get('GRAPHITE_RUNTIME_METRIC')

        return {
            "result": result_path.format(type_metric),
            "runtime": runtime_path.format(type_metric)
        }

    def _get_current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _get_alert_details(self, alert_action, reason):
        return {
            "action": alert_action,
            "service_key": self._pd_svc_key,
            "incident_key": self._pathjoin('sentinel', self.name, self._host),
            "description": ('Sentinel Error: Application {0} {1} on host {2}.'
                            .format(self.name, reason, self._host)),
            "details": ('Sentinel Error: Application {0} {1} on host {2}.\n'
                        'Review the application log and contact the appropriate'
                        ' development group.'
                        .format(self.name, reason, self._host))
        }

    @catch_exception(NoNodeError)
    @connected
    def _create_alert_node(self, alert_action, reason):
        """
        Create Node in ZooKeeper that will result in a PagerDuty alarm
        :type alert_action: zoom.common.types.AlertActionType
        """
        alert_details = self._get_alert_details(alert_action, reason)
        # path example: /foo/sentinel.bar.baz.HOSTFOO
        alert_path = self._pathjoin(
            self._settings.get('ZK_ALERT_PATH'),
            re.sub('/', '.', alert_details['incident_key'])
        )

        if self._env in self._settings.get('PAGERDUTY_ENABLED_ENVIRONMENTS'):
            self._log.info('Creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))

            if self.zkclient.exists(alert_path):
                self.zkclient.set(alert_path, value=json.dumps(alert_details))
            else:
                self.zkclient.create(alert_path, value=json.dumps(alert_details))
        else:
            self._log.info('Not creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))
            self._log.info('Would have created path {0}'.format(alert_path))

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
