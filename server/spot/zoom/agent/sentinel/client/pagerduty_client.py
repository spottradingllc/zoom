import re
import json
import os
from kazoo.exceptions import NoNodeError
import logging
from spot.zoom.agent.sentinel.util.helpers import verify_attribute
from spot.zoom.common.decorators import (
    connected,
    catch_exception,
)
from spot.zoom.common.types import (
    PlatformType
)


class PagerDuty(object):
    def __init__(self, config, settings, name, host, env, system, zkclient):
        self._config = config
        self._settings = settings
        self._name = name
        self._host = host
        self._env = env
        self._system = system
        self._zkclient = zkclient
        self._log = logging.getLogger('pd.{0}'.format(self.name))
        self._api = verify_attribute(self._config, 'pd_api',  )


    @catch_exception(NoNodeError)
    @connected
    def create_alert_node(self, alert_action, reason):
        """
        Create Node in ZooKeeper that will result in a PagerDuty alarm
        :type alert_action: spot.zoom.common.types.AlertActionType
        """
        alert_details = self._get_alert_details(reason)
        alert_details['action'] = alert_action
        # path example: /foo/sentinel.bar.baz.HOSTFOO
        alert_path = self._pathjoin(self._settings.get('ZK_ALERT_PATH'),
                                    re.sub('/', '.', alert_details['key']))

        if self._env in self._settings.get('PAGERDUTY_ENABLED_ENVIRONMENTS'):
            self._log.info('Creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))

            if self._zkclient.exists(alert_path):
                self._zkclient.set(alert_path, value=json.dumps(alert_details))
            else:
                self._zkclient.create(alert_path, value=json.dumps(alert_details))
        else:
            self._log.info('Not creating alert "{0}" node for env: {1}'
                           .format(alert_action, self._env))
            self._log.info('Would have created path {0}'.format(alert_path))

    def _get_alert_details(self, reason):
        return {
            "action": None,
            "subdomain": self._settings.get("PAGERDUTY_SUBDOMAIN"),
            "org_token": self._settings.get("PAGERDUTY_API_TOKEN"),
            "svc_token": self._settings.get("PAGERDUTY_SERVICE_TOKEN"),
            "key": self._pathjoin('sentinel', self._name, self._host),
            "description": 'Sentinel Error: Application {0} {1} on host '
                           '{2}.'.format(self._name, reason, self._host),
            "details": 'Sentinel Error: Application {0} {1} on host '
                       '{2}.\nReview the application log and contact the appropriate '
                       'development group.'.format(self._name, reason, self._host)
        }

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
