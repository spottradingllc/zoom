import json
import logging
import logging.config
import os
import socket

from zoom.common.constants import get_zk_conn_string, ZOOM_CONFIG
from zoom.agent.util.helpers import get_system, zk_path_join
from zoom.common.types import PlatformType


class Configuration(object):
    def __init__(self, zookeeper, **kwargs):
        """
        :type zookeeper: :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        self._zookeeper = zookeeper
        self._settings = kwargs
        try:
            data, stat = self._zookeeper.get(ZOOM_CONFIG)
            config = json.loads(data)

            # create 'logs' directory if it does not exist
            if not os.path.exists("logs"):
                os.makedirs("logs")

            # initialize logging
            logging_config = config.get('logging')
            logging.config.dictConfig(logging_config)

            # get system type
            running_os = self._get_system()

            self._host = socket.gethostname()
            # web_server
            web_server_settings = config.get('web_server')
            self._port = self._get_setting('port', web_server_settings.get('port'))
            self._is_debug = web_server_settings.get('debug')

            self._application_path = os.getcwd()
            self._client_path = zk_path_join((os.path.normpath(os.getcwd() + os.sep + os.pardir)), 'client')
            self._doc_path = zk_path_join((os.path.normpath(os.getcwd() + os.sep + os.pardir)), "doc")
            self._html_path = zk_path_join(self._client_path, "views")
            self._images_path = zk_path_join(self._client_path, "images")
            self._pid = os.getpid()
            self._environment = self._get_setting('environment',
                                                  os.environ.get('EnvironmentToUse', 'Staging'))

            # zookeeper
            zookeeper_settings = config.get('zookeeper')
            self._agent_configuration_path = zookeeper_settings.get('agent_configuration_path')
            self._agent_state_path = zookeeper_settings.get('agent_state_path')
            self._task_path = zookeeper_settings.get('task_path')
            self._application_state_path = zookeeper_settings.get('application_state_path')
            self._global_mode_path = zookeeper_settings.get('global_mode_path')
            self._pillar_path = zookeeper_settings.get('pillar_path')
            self._alert_path = zookeeper_settings.get('alert_path')
            self._override_node = zookeeper_settings.get('override_node', '/spot/software/config/override')
            self._zookeeper_host = get_zk_conn_string(self._environment)

            # pagerduty
            pagerduty_settings = config.get('pagerduty')
            self._pagerduty_default_svc_key = pagerduty_settings.get('pagerduty_default_svc_key')
            self._pagerduty_api_token = pagerduty_settings.get('pagerduty_api_token')
            self._pagerduty_subdomain = pagerduty_settings.get('pagerduty_subdomain')
            self._pagerduty_enabled_environments = pagerduty_settings.get('pagerduty_enabled_environments')
            self._pagerduty_alert_footer = pagerduty_settings.get('pagerduty_footer', '')

            # database
            db_settings = config.get('database')
            self._db_type = db_settings.get('db_type')
            if running_os == PlatformType.WINDOWS:
                self._sql_connection = db_settings.get('sql_connection_windows')
            elif running_os == PlatformType.LINUX:
                self._sql_connection = db_settings.get('sql_connection')

            # authentication
            ad_settings = config.get('active_directory')
            self._ldap_server = ad_settings.get('host')
            self._ldap_port = ad_settings.get('port')


            # environment specific
            env_settings = config.get(self._environment.lower())
            self._read_write_groups = env_settings.get('read_write_groups')
            self._graphite_host = env_settings.get('graphite_host')

            # chatops
            chatops_settings = env_settings.get('chatops', {})
            self._chatops_url = chatops_settings.get('url')
            self._chatops_group = chatops_settings.get('group')
            self._chatops_commands_to_chat = chatops_settings.get('commands_to_chat')


            # message throttling
            throttle_settings = config.get('message_throttle')
            self._throttle_interval = throttle_settings.get('interval')

            # salt
            self._salt_settings = env_settings.get('saltREST')

        except ValueError as e:
            logging.error('Data at {0} is not valid JSON.'.format(ZOOM_CONFIG))
            raise e
        except Exception as e:
            logging.exception('An unhandled exception occurred.')
            raise e

    def _get_system(self):
        sys = get_system()
        return sys

    def _get_setting(self, setting, default):
        s = self._settings.get(setting, None)
        if s is not None:
            return s
        else:
            return default

    @property
    def salt_settings(self):
        return self._salt_settings

    @property
    def application_path(self):
        return self._application_path

    @property
    def doc_path(self):
        return self._doc_path

    @property
    def client_path(self):
        return self._client_path

    @property
    def html_path(self):
        return self._html_path

    @property
    def images_path(self):
        return self._images_path

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
        return self._is_debug

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
    def alert_path(self):
        return self._alert_path

    @property
    def pagerduty_default_svc_key(self):
        return self._pagerduty_default_svc_key

    @property
    def pagerduty_api_token(self):
        return self._pagerduty_api_token

    @property
    def pagerduty_subdomain(self):
        return self._pagerduty_subdomain

    @property
    def pagerduty_enabled_environments(self):
        return self._pagerduty_enabled_environments

    @property
    def pagerduty_alert_footer(self):
        return self._pagerduty_alert_footer

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
        return self._read_write_groups

    @property
    def zookeeper_host(self):
        return self._zookeeper_host

    @property
    def throttle_interval(self):
        return self._throttle_interval

    @property
    def override_node(self):
        return self._override_node

    @property
    def graphite_host(self):
        return self._graphite_host

    @property
    def chatops_url(self):
        return self._chatops_url

    @property
    def chatops_group(self):
        return self._chatops_group

    @property
    def chatops_commands_to_chat(self):
        return self._chatops_commands_to_chat
