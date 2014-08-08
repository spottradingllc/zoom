import logging
import tornado.web
from httplib import INTERNAL_SERVER_ERROR
from zoom.utils.decorators import timethis


class ReloadCacheHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def post(self):
        try:
            logging.info("Clearing and reloading all server side caches")
            self.application.data_store.reload()
            self.write('Cache Reloaded')
            self.set_header('Content-Type', 'text/html')
        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)
