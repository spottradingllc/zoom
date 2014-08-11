import httplib
import logging
import tornado.web
from zoom.utils.decorators import timethis


class TimeEstimateHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def get(self):
        try:
            logging.info('Retrieving Timing Estimate')

            self.write(self.application.data_store.load_time_estimate_cache().to_json())

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
