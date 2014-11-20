import httplib
import json
import logging

import tornado.web

from spot.zoom.common.decorators import TimeThis


class PagerDutyServicesHandler(tornado.web.RequestHandler):
    @property
    def pd_client(self):
        """
        :rtype: spot.zoom.common.pagerduty.PagerDuty
        """
        return self.application.data_store.pd_client

    @TimeThis(__file__)
    def get(self):
        try:
            self.write(json.dumps(self.pd_client.get_service_dict()))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)