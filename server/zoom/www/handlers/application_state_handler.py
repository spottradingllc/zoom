import httplib
import json
import logging
import os.path

import tornado.web

from zoom.common.decorators import TimeThis


class ApplicationStateHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @property
    def application_state_cache(self):
        """
        :rtype: zoom.www.cache.application_state_cache.ApplicationStateCache
        """
        return self.application.data_store.application_state_cache

    @property
    def app_state_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.application_state_path

    @TimeThis(__file__)
    def get(self, path):
        """
        @api {get} /api/application/states/[:id] Get Application State
        @apiVersion 1.0.0
        @apiName GetAppState
        @apiGroup ApplicationState
        """
        try:
            logging.info('Retrieving Application State Cache for client {0}'
                         .format(self.request.remote_ip))
            result = self.data_store.load_application_state_cache()
            if path:
                if not path.startswith(self.app_state_path):
                    # be able to search by comp id, not full path
                    path = os.path.join(self.app_state_path, path[1:])
                item = result.application_states.get(path, {})
                self.write(item)
            else:
                self.write(result.to_json())

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')

    @TimeThis(__file__)
    def post(self, path):
        """
        @api {post} /api/application/states/:id Manually over-ride some value for an app state
        @apiParam {String} key The Application State key to over-ride
        @apiParam {String} value The Value to over-ride it with
        @apiVersion 1.0.0
        @apiName PostAppState
        @apiGroup ApplicationState
        """
        try:
            logging.info('Over-riding Application State Cache values client {0}'
                         .format(self.request.remote_ip))

            request = json.loads(self.request.body)
            key = request.get('key', None)
            value = request.get('value', None)
            logging.debug('Raw request: {0}'.format(request))

            if path is not None:
                self.application_state_cache.manual_update(path, key, value)
                self.set_status(httplib.OK)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)
