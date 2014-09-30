import logging
import pygerduty


class PagerDuty(object):
    """
    Create or resolve PagerDuty alerts.
    """
    def __init__(self, subdomain, organization_token, service_token):
        """
        :type subdomain: str
        :type organization_token: str
        :type service_token: str
        """
        self._log = logging.getLogger('pagerduty')
        self._pager = pygerduty.PagerDuty(subdomain,
                                          api_token=organization_token)
        self._org_token = organization_token
        self._svc_token = service_token

    def trigger(self, key, description, details):
        """
        :type key: str
        :type description: str
        :type details: str
        """
        try:
            self._log.info('Creating incident for key: {0}'.format(key))
            self._pager.trigger_incident(service_key=self._svc_token,
                                         incident_key=key,
                                         description=description,
                                         details=details)
        except Exception as ex:
            self._log.error('An Exception occurred trying to trigger '
                            'incident with key {0}: {1}'.format(key, ex))

    def resolve(self, key):
        """
        :type key: str
        """
        self._log.info('Resolving incident for key: {0}'.format(key))
        if key in self.get_open_incidents():
            try:
                self._pager.resolve_incident(service_key=self._svc_token,
                                             incident_key=key)
            except Exception as ex:
                self._log.error('An Exception occurred trying to resolve '
                                'incident with key {0}: {1}'.format(key, ex))

    def get_open_incidents(self):
        """
        :rtype: list
        """
        try:
            triggered = [incident.incident_key for incident in
                         self._pager.incidents.list(status="triggered")]
            acknowledged = [incident.incident_key for incident in
                            self._pager.incidents.list(status="acknowledged")]
            return triggered + acknowledged
        except Exception as ex:
            self._log.error('An Exception occurred trying to get open '
                            'incidents: {0}'.format(ex))
            return list()
