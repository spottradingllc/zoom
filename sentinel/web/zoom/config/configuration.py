import os
import json
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
                configuration_file_name = 'zoom.config'
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
            self._environment = os.environ.get('EnvironmentToUse', 'Staging')

            # zookeeper
            self._agent_configuration_path = safe_config_parser.get('zookeeper', 'agent_configuration_path')
            self._agent_state_path = safe_config_parser.get('zookeeper', 'agent_state_path')
            self._task_path = safe_config_parser.get('zookeeper', 'task_path')
            self._application_state_path = safe_config_parser.get('zookeeper', 'application_state_path')
            self._global_mode_path = safe_config_parser.get('zookeeper', 'global_mode_path')
            self._pillar_path = safe_config_parser.get('zookeeper', 'pillar_path')

            self._zookeeper_host = dict(
                staging = safe_config_parser.get('staging', 'host'),
                production = safe_config_parser.get('production', 'host')
            )

            # database
            self._db_type = safe_config_parser.get('database', 'db_type')
            self._sql_connection = safe_config_parser.get('database', 'sql_connection')

            # authentication
            self._ldap_server = safe_config_parser.get('active_directory', 'host')
            self._ldap_port = safe_config_parser.get('active_directory', 'port')
            self._read_write_groups = dict(
                staging = json.loads(safe_config_parser.get('staging', 'read_write_groups')),
                production = json.loads(safe_config_parser.get('production', 'read_write_groups')),
            )
            
            #graphite
            self._graphite_host = safe_config_parser.get('staging', 'graphite_host')

        except Exception as e:
            logging.exception(e)
            raise e

    @property
    def environment(self):
        return self._environment

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def ldap_url(self):
        return 'ldap://{0}:{1}'.format(self._ldap_server, self._ldap_port)

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
    def pillar_path(self):
        return self._pillar_path

    @property
    def db_type(self):
        return self._db_type

    @property
    def sql_connection(self):
        return self._sql_connection

    @property
    def global_mode_path(self):
        return self._global_mode_path

    @property
    def task_path(self):
        return self._task_path

    @property
    def read_write_groups(self):
        return self._read_write_groups.get(self._environment.lower())

    @property
    def zookeeper_host(self):
        return self._zookeeper_host.get(self._environment.lower())

    @property
    def graphite_host(self):
        return self._graphite_host
