import logging
import tornado.web
import os.path

from httplib import INTERNAL_SERVER_ERROR
from zoom.common.decorators import TimeThis


class TimeEstimateHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @property
    def app_state_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.application_state_path

    @TimeThis(__file__)
    def get(self, path):
        """
        @api {get} /api/timingestimate[/:path] Get an estimate on when all apps will be up
        @apiVersion 1.0.0
        @apiName GetEstimate
        @apiGroup Estimate
        """
        try:
            logging.info('Retrieving Timing Estimate')
            if path:
                if not path.startswith(self.app_state_path):
                    # be able to search by comp id, not full path
                    path = os.path.join(self.app_state_path, path[1:])

                self.write(self.data_store.get_start_time(path))
            else:
                self.write(self.data_store.load_time_estimate_cache().to_json())

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
