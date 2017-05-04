import logging
import json
import os
import resource
import signal
import socket
import sys
import time
import pprint
from multiprocessing import Lock
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

import tornado.httpserver
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import ZookeeperError, NodeExistsException
from kazoo.handlers.threading import SequentialThreadingHandler

from zoom.agent.web.rest import RestServer
from zoom.common.decorators import (
    connected,
    catch_exception,
    run_only_one
)
from zoom.agent.util.helpers import verify_attribute
from zoom.agent.entities.child_process import ChildProcess
from zoom.agent.task.zk_task_client import ZKTaskClient
from zoom.common.constants import (
    get_zk_conn_string,
    ZK_AGENT_CONFIG,
)
from zoom.agent.util.helpers import get_system, get_version


class SentinelDaemon(object):
    def __init__(self, port):
        """
        Read config and spawn child processes.
        :type port: int
        """
        self._log = logging.getLogger('sent.daemon')
        self._log.info('Creating Sentinel')

        self._port = port
        self.children = dict()
        self._settings = None
        self._system = get_system()
        self._hostname = socket.getfqdn()
        self._prev_state = None
        self.listener_lock = Lock()
        self.version = get_version()
        self.task_client = None

        self.zkclient = KazooClient(hosts=get_zk_conn_string(),
                                    timeout=60.0,
                                    handler=SequentialThreadingHandler(),
                                    logger=logging.getLogger('kazoo.daemon'))

        self.zkclient.add_listener(self._zk_listener)
        # this will run self._reset_after_connection_loss
        self.zkclient.start()
        while not self._settings:
            self._log.info('Waiting for settings.')
            time.sleep(1)

        self._tmp_dir = os.path.join(self._settings.get('zookeeper').get('temp_directory', '/'), 'ruok')

        self.task_client = ZKTaskClient(self.children,
                                        self.zkclient,
                                        self._settings.get('zookeeper', {}).get('task'))

        self._rest_server = tornado.httpserver.HTTPServer(RestServer(self.children,
                                                                     self.version,
                                                                     self._tmp_dir,
                                                                     self._hostname,
                                                                     self.zkclient))

        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._handle_sigint)
        self._log.info('Created Sentinel')

    def __enter__(self):
        logging.info('Starting Sentinel, listening on port {}'.format(self._port))
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        except ValueError, ve:
            logging.critical('Invalid resource limit specified. Core files will not be generated for apps: {0}'.format(ve))
        self._rest_server.listen(self._port)
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

    @connected
    def _get_settings(self, event=None):
        """
        Populate self._settings dict.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        data, stat = self.zkclient.get(ZK_AGENT_CONFIG,
                                       watch=self._reset_after_connection_loss)
        self._settings = json.loads(data)
        self._log.info('Got settings:\n{0}'
                       .format(pprint.pformat(self._settings)))

    @catch_exception(NodeExistsException)
    @connected
    def _register(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        # TODO: Do something if this path is not provided
        agent_state_path = self._settings.get('zookeeper', {}).get('agent_state')
        path = '/'.join([agent_state_path, self._hostname])
        components = {"components": self.children.keys()}
        if not self.zkclient.exists(path, watch=self._register):
            self.zkclient.create(path,
                                 value=json.dumps(components),
                                 ephemeral=True)
        else:
            try:
                data, stat = self.zkclient.get(path)
                registered_comps = json.loads(data)
            except ValueError:
                registered_comps = {}

            # register most recent components
            if components != registered_comps:
                self.zkclient.set(path, json.dumps(components))

        self._log.info('Done Registering: {}'.format(components))

    @connected
    def _get_config_and_run(self, event=None):
        """
        Grab config from Zookeeper. Spawn ChildProcess instances.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        # TODO: Do something if this path is not provided
        agent_config_path = self._settings.get('zookeeper', {}).get('agent_config')
        config_path = '/'.join([agent_config_path, self._hostname])
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
            self._register()

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
                    'process': ChildProcess(component,
                                            self._system,
                                            self._settings)
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

        # sent stop to all, now wait for all to complete
        map(lambda i: i.join(), [x['process'] for x in self.children.values()])
        self.children.clear()

    @catch_exception(Exception, traceback=True)
    @run_only_one('listener_lock')
    @connected
    def _reset_after_connection_loss(self):
        """
        Used for spawning child process and resetting watches ZK connection
        changes. This includes the first connection to Zookeeper (on startup).
        """
        self._log.info('Daemon listener callback triggered')
        self._get_settings()
        self._get_config_and_run()
        if self.task_client is not None:
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
            if self._prev_state == KazooState.LOST and state == KazooState.CONNECTED:
                self.zkclient.handler.spawn(self._reset_after_connection_loss)
            elif self._prev_state == KazooState.CONNECTED and state == KazooState.SUSPENDED:
                pass
            elif self._prev_state == KazooState.CONNECTED and state == KazooState.LOST:
                pass
            elif self._prev_state == KazooState.SUSPENDED and state == KazooState.LOST:
                pass
            elif self._prev_state == KazooState.SUSPENDED and state == KazooState.CONNECTED:
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

