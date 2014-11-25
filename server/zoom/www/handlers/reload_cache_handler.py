import logging
import tornado.web
from httplib import INTERNAL_SERVER_ERROR

from zoom.common.decorators import TimeThis


class ReloadCacheHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def post(self):
        try:
            user = self.get_argument("user")
            command = self.get_argument("command")

            logging.info("Received reload cache command for target '{0}' from "
                         "user {1}:{2}"
                         .format(command, user, self.request.remote_ip))
            logging.info("Clearing and reloading all server side caches")
            self.data_store.reload()
            self.write('Cache Reloaded')
            self.set_header('Content-Type', 'text/html')
        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)
