import logging
import pygerduty


class PagerDuty(object):
    """
    Create or resolve PagerDuty alerts.
    """
    def __init__(self, subdomain, organization_token, default_svc_key,
                 alert_footer=''):
        """
        :type subdomain: str
        :type organization_token: str
        :type default_svc_key: str
        :type alert_footer: str
        """
        self._log = logging.getLogger('pagerduty')
        self._pager = pygerduty.PagerDuty(subdomain,
                                          api_token=organization_token)
        self._org_token = organization_token
        self._default_svc_key = default_svc_key  # Zoom Service api key
        self._alert_footer = alert_footer

    def trigger(self, svc_key, incident_key, description, details):
        """
        :type svc_key: str
        :type incident_key: str
        :type description: str
        :type details: str
        """
        full_details = details + '\n' + self._alert_footer
        try:
            if svc_key is None:
                svc_key = self._default_svc_key
            self._log.info('Creating incident for api key: {0}'
                           ' and incident key: {1}'
                           .format(svc_key, incident_key))
            self._pager.trigger_incident(service_key=svc_key,
                                         incident_key=incident_key,
                                         description=description,
                                         details=full_details)
        except Exception as ex:
            self._log.error('An Exception occurred trying to trigger incident '
                            'with key {0}: {1}'.format(incident_key, ex))

    def resolve(self, svc_key, incident_key):
        """
        :type svc_key: str
        :type incident_key: str
        """
        if svc_key is None:
            svc_key = self._default_svc_key
        self._log.info('Resolving incident for api key: {0}'
                       ' and incident key: {1}'.format(svc_key, incident_key))
        if incident_key in self.get_open_incidents():
            try:
                self._pager.resolve_incident(service_key=svc_key,
                                             incident_key=incident_key)
            except Exception as ex:
                self._log.error('An Exception occurred trying to resolve '
                                'incident with key {0}: {1}'
                                .format(incident_key, ex))

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

    def get_service_dict(self):
        """
        Return dict of configured services in PagerDuty
        :rtype: dict
        """
        pd_service_dict = {}
        pd_services = self._pager.services.list(limit=100)
        for pd_service in pd_services:
            if pd_service.email_incident_creation is None:
                pd_service_dict[pd_service.name] = pd_service.service_key
        return pd_service_dict
