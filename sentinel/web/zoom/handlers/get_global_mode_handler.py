import httplib
import json
import logging
import tornado.web


class GetGlobalModeHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            result = self.application.data_store.get_global_mode()

            self.write(result)

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')
