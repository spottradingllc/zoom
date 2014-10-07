import logging
import tornado.web

from httplib import INTERNAL_SERVER_ERROR
from spot.zoom.common.decorators import TimeThis


class TimeEstimateHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: spot.zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def get(self):
        try:
            logging.info('Retrieving Timing Estimate')

            self.write(self.data_store.load_time_estimate_cache().to_json())

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
