import httplib
import logging
import os.path
import tornado.web

from zoom.common.decorators import TimeThis


class HostMappingHandler(tornado.web.RequestHandler):
    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def get(self, path):
        ret = {"method": 'GET', "query": path, "code": httplib.OK,
               "data": None, "error": None}
        try:
            logging.info('Retrieving Application Mapping for client {0}'
                         .format(self.request.remote_ip))
            state_cache = self.data_store.load_application_state_cache()
            mapping = self.data_store.application_state_cache.host_mapping

            res = mapping.get(path, None)

            out = list()
            if res is not None:
                for k in res.keys():
                    d = state_cache.application_states.get(k, None)
                    if d is not None:
                        out.append(d.get('application_name'))

            ret['data'] = out

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            ret['code'] = httplib.INTERNAL_SERVER_ERROR
            ret['error'] = str(e)
            logging.exception(e)
        finally:
            self.write(ret)

        self.set_header('Content-Type', 'application/json')

class ApplicationMappingHandler(tornado.web.RequestHandler):
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
        ret = {"method": 'GET', "query": path, "code": httplib.OK,
               "data": None, "error": None}
        try:
            logging.info('Retrieving Application Mapping for client {0}'
                         .format(self.request.remote_ip))
            state_cache = self.data_store.load_application_state_cache()
            if path:
                if not path.startswith(self.app_state_path):
                    # be able to search by comp id, not full path
                    path = os.path.join(self.app_state_path, path[1:])

                state = state_cache.application_states.get(path, None)
                if state is not None:
                    ret['data'] = state.get('application_host')

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            ret['code'] = httplib.INTERNAL_SERVER_ERROR
            ret['error'] = str(e)
            logging.exception(e)
        finally:
            self.write(ret)

        self.set_header('Content-Type', 'application/json')