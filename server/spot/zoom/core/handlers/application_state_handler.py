import httplib
import json
import logging

import tornado.web

from spot.zoom.core.utils.decorators import timethis


class ApplicationStateHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def get(self):
        try:
            logging.info('Retrieving Application State Cache')
            result = self.application.data_store.load_application_state_cache()
            self.write(result.to_json())

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
