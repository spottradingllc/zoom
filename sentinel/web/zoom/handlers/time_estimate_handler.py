import httplib
import json
import logging
import requests
import tornado.web
from zoom.entities.types import DependencyType
from zoom.utils.decorators import timethis


class TimeEstimateHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def get(self):
        try:
            logging.info('Retrieving Timing Estimate')

            self.write(json.dumps(self.application.data_store.load_time_estimate_cache()))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')

