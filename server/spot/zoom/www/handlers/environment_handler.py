import json
import logging
import httplib
import tornado.web
import tornado.httpclient

from spot.zoom.common.decorators import TimeThis


class EnvironmentHandler(tornado.web.RequestHandler):
    @property
    def environment(self):
        """
        :rtype: str
        """
        return self.application.configuration.environment

    @TimeThis(__file__)
    def get(self):
        try:

            self.write({'environment': self.environment})

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
