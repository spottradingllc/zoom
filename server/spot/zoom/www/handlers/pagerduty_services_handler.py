import httplib
import json
import logging

import tornado.web

from spot.zoom.common.decorators import TimeThis


class PagerDutyServicesHandler(tornado.web.RequestHandler):
    @TimeThis(__file__)
    def get(self):
        try:
            self.write(json.dumps(self.application.pd.get_service_dict()))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)