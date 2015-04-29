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

        logging.info('Retrieving Application Operational Dependency Cache for '
                     'client {0}'.format(self.request.remote_ip))
        try:
            # append the service we want opdep for to the array
            opdep_array.append(path)
            if path:
                opdep_array = self._downstream_recursive(path, opdep_array)
                opdep_dict['opdep'] = opdep_array
                self.write(opdep_dict)
            else:
                self.write('Please specify a path for operational '
                           'dependency lookup')

        except Exception as e:
            logging.exception(e)
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))

        self.set_header('Content-Type', 'application/json')
        logging.info('Done Retrieving Application Depends Cache')

    def _downstream_recursive(self, parent_path, opdep_array):
        app_cache = self.data_store.load_application_dependency_cache()
        item = app_cache.application_dependencies.get(parent_path, {})

        for downstream in item.get("downstream", None):
            item = app_cache.application_dependencies.get(downstream, {})
            for dependency in item.get('dependencies', None):
                # Checks both HasChildren and HasGrandChildren predicates
                if dependency.get('path', None) in parent_path:
                    if dependency.get('operational', None) is True:
                        # only append elements not in the array
                        if downstream not in opdep_array:
                            opdep_array.append(downstream)
                        # Recursive with the operational downstream path
                        self._downstream_recursive(downstream, opdep_array)
                    else:
                        logging.debug('{0} is not operational '
                                      'dependency of {1}'
                                      .format(parent_path, downstream))

        return opdep_array


