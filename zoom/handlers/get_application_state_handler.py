import httplib
import json
import logging

import tornado.web


class GetApplicationStateHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            result = self.application.data_store.load_application_state_cache()

            self.write(json.dumps(result))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.error(e)

        self.set_header('Content-Type', 'application/json')
