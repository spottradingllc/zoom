import logging
import json
import os.path
import platform

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import NoNodeError, NodeExistsError
from kazoo.handlers.threading import SequentialThreadingHandler
from multiprocessing import Lock
from time import sleep

from sentinel.action.factory import ActionFactory
from sentinel.config.constants import (
    ZK_AGENT_STATE_PATH,
    ZK_STATE_PATH,
    ZK_CONN_STRING,
    ZK_CONFIG_PATH,
    ZK_GLOBAL_PATH,
    ALLOWED_WORK
)
from sentinel.common.enum import (
    SimpleObject,
    ApplicationMode,
    PlatformType,
    ApplicationState
)
from sentinel.util.decorators import (
    connected,
    time_this,
    catch_exception,
    run_only_one
)
from sentinel.util.helpers import verify_attribute
from sentinel.common.work_manager import WorkManager
from sentinel.common.task import Task

if 'Linux' in platform.platform():
    from sentinel.client.process_client import ProcessClient
else:
    from sentinel.client.process_client import WindowsProcessClient as ProcessClient


class Application(object):
    """
    Service object to represent an deployed service.
    """
    def __init__(self, config, conn, queue, system, application_type):
        """
        :type config: dict (xml)
        :type conn: multiprocessing.Connection
        :type queue: sentinel.common.unique_queue.UniqueQueue
        :type system: sentinel.common.enum.PlatformType
        :type application_type: sentinel.common.enum.ApplicationType
        """
        self.config = config
        self.name = verify_attribute(self.config, 'id', none_allowed=False)
        self._log = logging.getLogger('sent.{0}.app'.format(self.name))
        # informational attributes
        self._host = platform.node()
        self._system = system
        self._predicates = list()
        self._running = True  # used to manually stop the run loop
        self._prev_state = None
        self._actions = dict()  # created in _reset_watches on zk connect

        # tool-like attributes
        self.listener_lock = Lock()
        self._action_queue = queue
        self._mode = ApplicationMode(ApplicationMode.MANUAL)
        self._state = SimpleObject(ApplicationState.OK)
        self._start_allowed = SimpleObject(False)  # allowed_instances
        self._run_check_mode = False

        self._allowed_instances = self._init_allowed_inst(self.config)
        self._paths = self._init_paths(self.config, application_type)

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
                                                   application_type)

        self._actions = self._init_actions()
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
                                     value=self._host,
                                     makepath=True)

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
    def start(self, reset=True, pause=False, **kwargs):
        """
        Start actual process
        This is called by REST
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        if reset:
            self._proc_client.reset_counters()
        if pause:
            self.ignore()

        self._state.set_value(ApplicationState.STARTING)
        self._update_agent_node_with_app_details()

        result = self._proc_client.start()

        if self._run_check_mode:  # Reset to global mode if restart with dep
            self._check_mode()
            self._run_check_mode = False

        if result != 0:
            self._state.set_value(ApplicationState.ERROR)
        else:
            self._state.set_value(ApplicationState.OK)

        self._update_agent_node_with_app_details()

        return result

    @time_this
    def stop(self, reset=True, pause=False, **kwargs):
        """
        Stop actual process
        This is called by REST
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        if reset:
            self._proc_client.reset_counters()
        if pause:
            self.ignore()

        self._state.set_value(ApplicationState.STOPPING)
        self._update_agent_node_with_app_details()

        result = self._proc_client.stop(kwargs)

        if result != 0 and not kwargs:
            self._state.set_value(ApplicationState.ERROR)
        else:
            self._state.set_value(ApplicationState.OK)

        self._update_agent_node_with_app_details()

        return result

    def restart(self, reset=True, pause=False, **kwargs):
        """
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        self.stop(reset=reset, pause=pause, **kwargs)
        self.start(reset=reset, pause=pause, **kwargs)

    def dep_restart(self, **kwargs):
        self._run_check_mode = True # only used in self.start()
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
        :param kwargs: passed from zoom.handlers.control_agent_handlers
        """
        self._mode.set_value(ApplicationMode.MANUAL)
        self._log.info('Mode is now "{0}"'.format(self._mode))
        self._update_agent_node_with_app_details()
        return 0

    @time_this
    @connected
    def react(self, **kwargs):
        """
        :param kwargs: passed from zoom.handlers.control_agent_handlers
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

    @connected
    def _update_agent_node_with_app_details(self, event=None):
        """
        Register app data with the agent in the state tree.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        if self.zkclient.exists(self._paths['zk_agent_path'],
                                watch=self._update_agent_node_with_app_details):
            data, stat = self.zkclient.get(self._paths['zk_agent_path'])

            agent_apps = json.loads(data)

            current_data = {'name': self.name,
                            'host': self._host,
                            'platform': self._system,
                            'register_path': self._paths['zk_state_base'],
                            'mode': self._mode.value,
                            'state': self._state.value}

            # make sure data is the most recent
            if current_data != agent_apps.get(self.name, None):
                agent_apps[self.name] = current_data
                self.zkclient.set(self._paths['zk_agent_path'],
                                  json.dumps(agent_apps))
                self._log.debug('Registering {0}'.format(agent_apps))

    def _init_paths(self, config, atype):
        """
        :rtype: dict
        """
        paths = dict()
        registrationpath = verify_attribute(config, 'registrationpath',
                                            none_allowed=True)

        if registrationpath is not None:
            paths['zk_state_base'] = registrationpath
        else:
            paths['zk_state_base'] = self._pathjoin(ZK_STATE_PATH, atype,
                                                    self.name)

        paths['zk_state_path'] = self._pathjoin(paths['zk_state_base'],
                                                self._host)
        paths['zk_config_path'] = self._pathjoin(ZK_CONFIG_PATH, atype,
                                                 self.name)
        paths['zk_agent_path'] = self._pathjoin(ZK_AGENT_STATE_PATH, self._host)
        paths['graphite_type_metric'] = self._get_graphite_type_metric(
                                                 paths['zk_state_base'])

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

    def _init_proc_client(self, config, atype):
        """Create the process client."""
        command = verify_attribute(config, 'command', none_allowed=True)
        script = verify_attribute(config, 'script', none_allowed=True)
        restartmax = verify_attribute(config, 'restartmax', none_allowed=True,
                                      cast=int)
        restart_on_crash = verify_attribute(config, 'restartoncrash', none_allowed=True)
        
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
                             graphite_app_metric=self._paths['graphite_type_metric']
                             )

    def _init_actions(self):
        """
        :rtype: dict
        """
        action_factory = ActionFactory(component=self,
                                       zkclient=self.zkclient,
                                       proc_client=self._proc_client,
                                       action_queue=self._action_queue,
                                       mode=self._mode,
                                       system=self._system,
                                       pred_list=self._predicates)
        return action_factory.create(self.config)

    def _init_work_manager(self, queue, pipe):
        """
        :rtype: sentinel.common.work_manager.WorkManager
        """
        acceptable_work = dict()
        for w in ALLOWED_WORK:
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
            data, stat = self.zkclient.get(self._paths['zk_state_base'],
                                           watch=self._check_allowed_instances)
            if not(stat.numChildren < self._allowed_instances):
                self._log.info('Running instances of {0} ({1}) is >= allowed '
                               'instances ({2}).'
                               .format(self.name, stat.numChildren,
                                       self._allowed_instances))
                self._start_allowed.set_value(False)
 
            else:
                self._log.info('Running instances of {0} ({1}) is < '
                               'allowed instances ({2}). It should be allowed '
                               'to start.'.format(self.name, stat.numChildren,
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
        modepath = self._pathjoin(ZK_GLOBAL_PATH, 'mode')
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
        type_path = state_path.split('state/',1)[1]
        type_metric = type_path.replace('/', '.')
        return type_metric

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
            self._actions = self._init_actions()
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
