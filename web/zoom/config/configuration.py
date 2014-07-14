import os
import logging
import logging.config
import socket

from ConfigParser import SafeConfigParser


class Configuration(object):
    def __init__(self, args):
        """
        :type args: list
        """
        try:
            # default configuration file
            if len(args) == 0:
                configuration_file_name = 'zoom/config/zoom.config'
            else:
                # override default configuration file
                configuration_file_name = args[0]

            safe_config_parser = SafeConfigParser()
            safe_config_parser.read(configuration_file_name)

            # create 'logs' directory if it does not exist
            if not os.path.exists("logs"):
                os.makedirs("logs")

            # initialize logging
            logging.config.fileConfig(configuration_file_name)

            self._host = socket.gethostname()
            self._port = safe_config_parser.get('web_server', 'port')
            self._is_debug = safe_config_parser.get('web_server', 'debug')
            self._directory = os.getcwd()
            self._pid = os.getpid()

            # zookeeper
            self._agent_configuration_path = safe_config_parser.get('zookeeper', 'agent_configuration_path')
            self._agent_state_path = safe_config_parser.get('zookeeper', 'agent_state_path')
            self._application_state_path = safe_config_parser.get('zookeeper', 'application_state_path')
            self._global_mode_path = safe_config_parser.get('zookeeper', 'global_mode_path')

            self._zookeeper_host = dict(
                staging = safe_config_parser.get('staging', 'host'),
                production = safe_config_parser.get('production', 'host')
            )

        except Exception as e:
            logging.error(e)
            raise e

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def is_debug(self):
        return self._is_debug.lower() == "true"

    @property
    def directory(self):
        return self._directory

    @property
    def pid(self):
        return self._pid

    @property
    def agent_configuration_path(self):
        return self._agent_configuration_path

    @property
    def agent_state_path(self):
        return self._agent_state_path

    @property
    def application_state_path(self):
        return self._application_state_path

    @property
    def global_mode_path(self):
        return self._global_mode_path

    def zookeeper_host(self, environment):
        if environment not in self._zookeeper_host:
            return self._zookeeper_host['staging']
        else:
            return self._zookeeper_host[environment]
