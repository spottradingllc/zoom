import logging
import pygerduty


class PagerDuty(object):
    """
    Create or resolve PagerDuty alerts.
    """
    def __init__(self, subdomain, organization_token, default_service_token):
        """
        :type subdomain: str
        :type organization_token: str
        :type service_token: str
        """
        self._log = logging.getLogger('pagerduty')
        self._pager = pygerduty.PagerDuty(subdomain,
                                          api_token=organization_token)
        self._org_token = organization_token
        self._default_svc_token = default_service_token

    def trigger(self, svc_token, key, description, details):
        """
        :type key: str
        :type description: str
        :type details: str
        """
        try:
            self._log.info('Creating incident for key: {0}'.format(key))
            api_key = self.look_up_api_key(svc_token)
            logging.info('### Found api key: {0}'.format(api_key))
            # self._pager.trigger_incident(service_key=api_key,
            #                              incident_key=key,
            #                              description=description,
            #                              details=details)
        except Exception as ex:
            self._log.error('An Exception occurred trying to trigger '
                            'incident with key {0}: {1}'.format(key, ex))

    def resolve(self, svc_token, key):
        """
        :type key: str
        """
        self._log.info('Resolving incident for key: {0}'.format(key))
        api_key = self.look_up_api_key(svc_token)
        logging.info('### FFound api key: {0}'.format(api_key))
        if key in self.get_open_incidents():
            try:
                self._pager.resolve_incident(service_key=api_key,
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

    def look_up_api_key(self, svc_token):
        pd_service_dict = {}
        self._pager.services.show('ATE')
        pd_services = self._pager.services.list()
        for pd_service in pd_services:
            pd_service_dict[pd_service.name] = pd_service.service_key

        return pd_service_dict(svc_token, self._default_svc_token)