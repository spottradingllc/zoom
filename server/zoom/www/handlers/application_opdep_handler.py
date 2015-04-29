import json
import logging
import httplib
import tornado.web

from zoom.common.decorators import TimeThis


class ApplicationOpDepHandler(tornado.web.RequestHandler):


    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def get(self, path):
        opdep_array = []
        opdep_dict = {}

        logging.info('Retrieving Application Dependency Cache for client {0}'
                     .format(self.request.remote_ip))
        try:
            opdep_array.append(path)
            result = self.data_store.load_application_dependency_cache()
            if path:
                array = self._downstream_recursive(path, opdep_array)
                opdep_dict['opdep'] = array
                self.write(opdep_dict)
            else:
                self.write(result.to_json())

        except Exception as e:
            logging.exception(e)
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))

        self.set_header('Content-Type', 'application/json')
        logging.info('Done Retrieving Application Depends Cache')

    def _downstream_recursive(self, parent_path, opdep_array):

        result = self.data_store.load_application_dependency_cache()
        item = result.application_dependencies.get(parent_path, {})

        for downstream in item.get("downstream", None):
            item = result.application_dependencies.get(downstream, {})
            for dependency in item.get('dependencies', None):
                if dependency.get('path', None) in parent_path:
                    if dependency.get('operational', None) is True:
                        if downstream not in opdep_array:
                            opdep_array.append(downstream)  # CHECK UNIQUENESS
                        #recursive since found
                        self._downstream_recursive(downstream, opdep_array)
                    else:
                        logging.info('### FALSE -- NOT operational')
                else:
                    logging.info('### FALSE')

        return opdep_array


