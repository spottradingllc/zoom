import logging
import pygerduty


class PagerDuty(object):
    def __init__(self, subdomain, organization_token, service_token):
        self._log = logging.getLogger('pagerduty')
        self._pager = pygerduty.PagerDuty(subdomain,
                                          api_token=organization_token)
        self._org_token = organization_token
        self._svc_token = service_token

    def trigger(self, key, description, details):
        self._log.info('Creating incident for key: {0}'.format(key))
        self._pager.trigger_incident(service_key=self._svc_token,
                                     incident_key=key,
                                     description=description,
                                     details=details)

    def resolve(self, key):
        self._log.info('Resolving incident for key: {0}'.format(key))
        if key in self.get_open_incidents():
            self._pager.resolve_incident(service_key=self._svc_token,
                                         incident_key=key)

    def get_open_incidents(self):
        return [incident.incident_key for incident in
                self._pager.incidents.list(status="triggered, acknowledged")]
