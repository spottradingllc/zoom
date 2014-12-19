import httplib
import json
import logging
import os.path

import tornado.web

from zoom.common.decorators import TimeThis
from zoom.agent.util.helpers import zk_path_join


class PagerExceptionsHandler(tornado.web.RequestHandler):
    @property
    def app_state_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.application_state_path

    @property
    def alert_exceptions(self):
        """
        :rtype: list
        """
        return self.application.data_store.alert_exceptions

    @property
    def application_state_cache(self):
        """
        :rtype: zoom.www.cache.application_state_cache.ApplicationStateCache
        """
        return self.application.data_store.application_state_cache

    @TimeThis(__file__)
    def get(self, comp_id):
        try:
            self.write(json.dumps(self.alert_exceptions))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

    @TimeThis(__file__)
    def post(self, comp_id):
        try:
            if comp_id is not None and comp_id not in self.alert_exceptions:
                logging.info('Adding PD exception for {0}'.format(comp_id))
                self.alert_exceptions.append(comp_id)
                self._update_app_state(comp_id, True)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

    @TimeThis(__file__)
    def delete(self, comp_id):
        try:
            if comp_id is not None and comp_id in self.alert_exceptions:
                logging.info('Removing PD exception for {0}'.format(comp_id))
                self.alert_exceptions.remove(comp_id)
                self._update_app_state(comp_id, False)

        except ValueError:
            pass
        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

    def _update_app_state(self, comp_id, value):
        path = zk_path_join(self.app_state_path, comp_id)
        self.application_state_cache.manual_update(path, 'pd_disabled', value)