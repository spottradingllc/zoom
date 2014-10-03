import json
import logging
import httplib
import tornado.web
import tornado.httpclient

from spot.zoom.common.decorators import TimeThis


class EnvironmentHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        return self.application.configuration

    @TimeThis(__file__)
    def get(self):
        try:
            message = {'environment': self.configuration.environment}

            self.write(json.dumps(message))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
