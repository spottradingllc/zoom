import logging
import tornado.web

from httplib import INTERNAL_SERVER_ERROR
from spot.zoom.www.utils.decorators import timethis


class TimeEstimateHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def get(self):
        try:
            logging.info('Retrieving Timing Estimate')

            self.write(self.application.data_store.load_time_estimate_cache())

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
