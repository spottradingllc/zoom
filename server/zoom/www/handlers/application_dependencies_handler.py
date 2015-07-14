import os.path
import json
import logging
import httplib
import tornado.web

from zoom.common.decorators import TimeThis


class ApplicationDependenciesHandler(tornado.web.RequestHandler):

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
        @api {get} /api/application/dependencies/[:id] Get Application's dependencies
        @apiVersion 1.0.0
        @apiName GetAppDep
        @apiGroup Dependency
        """
        logging.info('Retrieving Application Dependency Cache for client {0}'
                     .format(self.request.remote_ip))
        try:
            result = self.data_store.load_application_dependency_cache()
            if path:
                if not path.startswith(self.app_state_path):
                    # be able to search by comp id, not full path
                    path = os.path.join(self.app_state_path, path[1:])

                item = result.application_dependencies.get(path, {})
                self.write(item)
            else:
                self.write(result.to_json())

        except Exception as e:
            logging.exception(e)
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))

        self.set_header('Content-Type', 'application/json')
        logging.info('Done Retrieving Application Depends Cache')
