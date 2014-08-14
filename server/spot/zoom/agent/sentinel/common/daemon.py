import logging
import json
import signal
import sys
import platform
from multiprocessing import Lock
import tornado.httpserver

from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import ZookeeperError, NodeExistsException
from kazoo.handlers.threading import SequentialThreadingHandler
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

from spot.zoom.agent.sentinel.web.rest import RestServer
from spot.zoom.agent.sentinel.util.decorators import (
    connected,
    catch_exception,
    run_only_one
)
from spot.zoom.agent.sentinel.util.helpers import verify_attribute
from spot.zoom.agent.sentinel.common.child_process import ChildProcess
from spot.zoom.agent.sentinel.common.enum import PlatformType
from spot.zoom.agent.sentinel.client.task_client import TaskClient
from spot.zoom.agent.sentinel.config.constants import (
    ZK_CONN_STRING,
    ZK_AGENT_CONFIG_PATH,
    ZK_AGENT_STATE_PATH
)


class SentinelDaemon(object):
    def __init__(self):
        """
        Read config and spawn child processes.
        """
        self._log = logging.getLogger('sent.daemon')
        self._log.info('Creating Sentinel')

        self.children = dict()
        self._system = self._get_system()
        self._hostname = platform.node().upper()  # must be uppercase
        self._prev_state = None
        self.listener_lock = Lock()

        if self._system == PlatformType.LINUX:
            self.zkclient = KazooClient(hosts=ZK_CONN_STRING,
                                        handler=SequentialThreadingHandler(),
                                        logger=logging.getLogger('kazoo.daemon'))
        elif self._system == PlatformType.WINDOWS:
            self.zkclient = KazooClient(hosts=ZK_CONN_STRING,
                                        handler=SequentialThreadingHandler())

        self.zkclient.add_listener(self._zk_listener)
        self.zkclient.start()

        self.task_client = TaskClient(children=self.children,
                                      zkclient=self.zkclient)

        self._rest_server = tornado.httpserver.HTTPServer(
            RestServer(self.children))

        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._handle_sigint)
        self._log.info('Created Sentinel')

    def __enter__(self):
        logging.info('Starting Sentinel')
        self._rest_server.listen('9000')
        logging.info('Started Sentinel')

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def stop(self):
        """Terminate all child processes and exit."""
        self._log.info('Stopping Sentinel')
        self._terminate_children()
        self._rest_server.stop()
        self._log.info('Stopped Sentinel. Exiting.')
        sys.exit(0)

    def _handle_sigint(self, sig, frame):
        self._log.info('Caught signal %s.' % sig)
        self.stop()

    @catch_exception(NodeExistsException)
    @connected
    def _register(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        path = '/'.join([ZK_AGENT_STATE_PATH, self._hostname])
        if not self.zkclient.exists(path, watch=self._register):
            self.zkclient.create(path,
                                 value=json.dumps({}),
                                 ephemeral=True)

    @connected
    def _get_config_and_run(self, event=None):
        """
        Grab config from Zookeeper. Spawn ChildProcess instances.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        config_path = '/'.join([ZK_AGENT_CONFIG_PATH, self._hostname])
        try:
            if not self.zkclient.exists(config_path,
                                        watch=self._get_config_and_run):
                self._log.warning('Node does not exist at: {0}. Creating.'
                                  .format(config_path))
                self.zkclient.create(
                    config_path, value='<?xml version= "1.0"?><Application />')
                return

            data, stat = self.zkclient.get(config_path)
            config = ElementTree.fromstring(data.strip())
            
            self._terminate_children()
            self._spawn_children(config)

        except ParseError as e:
            self._log.error('Incomplete XML config found in path {0}: {1}'
                            .format(config_path, e))
        except ZookeeperError as e:
            self._log.error('ZK server returned a non-zero error code: {0}'
                            .format(e))
        except Exception as e:
            self._log.exception('There were some Exception: {0}'.format(e))

    def _spawn_children(self, config):
        """
        Populate the self.children dictionary
        :type config: xml.etree.ElementTree.Element
        """
        for component in config.iter('Component'):
            try:
                name = verify_attribute(component, 'id')
                self._log.info('Spawning %s' % name)
                self.children[name] = {
                    'config': component,
                    'process': ChildProcess(component, self._system)
                }

            except ValueError as e:
                self._log.error('Error with ID in config: {0}'.format(e))
                continue

    def _terminate_children(self):
        """
        Stop all children in the self.children dictionary, and clear it.
        """
        self._log.info('Stopping children.')
        for child in self.children.values():
            process = child['process']
            self._log.info('Terminating child -- {0}'.format(process))
            process.stop()
        self.children.clear()

    @run_only_one('listener_lock')
    @connected
    def _reset_after_connection_loss(self):
        """
        Used for spawning child process and resetting watches ZK connection
        changes. This includes the first connection to Zookeeper (on startup).
        """
        self._log.info('Daemon listener callback triggered')
        self._register()
        self._get_config_and_run()
        self.task_client.reset_watches()
        self._log.info('Daemon listener callback complete!')
                
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
            if (self._prev_state == KazooState.LOST
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
        except Exception as e:
            self._log.error('Listener excepted out with error: {0}'.format(e))

    def _get_system(self):
        system_str = platform.platform(terse=True)
        if 'Linux' in system_str:
            return PlatformType.LINUX
        elif 'Windows' in system_str:
            return PlatformType.WINDOWS
        else:
            return PlatformType.UNKNOWN
