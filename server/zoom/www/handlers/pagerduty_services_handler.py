import httplib
import json
import logging

import tornado.web

from zoom.common.decorators import TimeThis


class PagerDutyServicesHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def get(self):
        try:
            self.write(json.dumps(self.data_store.pagerduty_services))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)