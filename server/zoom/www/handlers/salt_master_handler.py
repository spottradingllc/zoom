import json
import logging
import httplib
import tornado.web
import tornado.httpclient

from zoom.common.decorators import TimeThis


class SaltMasterHandler(tornado.web.RequestHandler):
    @property
    def environment(self):
        """
        :rtype: str
        """
        return self.application.configuration.environment

    def salt(self):
        """
        :rtype: str
        """
        return self.application.configuration.salt_settings

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/v1/saltmaster/ Get salt settings
        @apiVersion 1.0.0
        @apiName GetSaltSettings
        @apiGroup Salt
        """
        try:
            self.write({'salt': self.salt()})

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
