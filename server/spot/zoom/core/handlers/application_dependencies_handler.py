import json
import logging
import httplib
import tornado.web

from spot.zoom.core.utils.decorators import timethis


class ApplicationDependenciesHandler(tornado.web.RequestHandler):

    @property
    def data_store(self):
        return self.application.data_store

    @timethis(__file__)
    def get(self):
        logging.info('Retrieving Application Dependency Cache')
        try:
            result = self.data_store.load_application_dependency_cache()

            self.write(result.to_json())

        except Exception as e:
            logging.exception(e)
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))

        self.set_header('Content-Type', 'application/json')
        logging.info('Done Retrieving Application Depends Cache')
