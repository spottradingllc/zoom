import json
import logging
import httplib
import tornado.web
import tornado.httpclient

from kazoo.exceptions import NoNodeError

from spot.zoom.agent.sentinel.common.thread_safe_object import ApplicationMode
from spot.zoom.www.utils.decorators import TimeThis


class GlobalModeHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk

    @property
    def configuration(self):
        return self.application.configuration

    @TimeThis(__file__)
    def get(self):
        try:
            message = self.application.data_store.get_global_mode()

            self.write(message.to_json())

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')

    @TimeThis(__file__)
    def post(self):
        """
        Set global Mode
        """
        try:
            # parse JSON dictionary from POST
            command = self.get_argument("command")
            user = self.get_argument("user")

            logging.info("Received {0} config for Zookeeper from user '{1}'"
                         .format(command, user))

            if command == ApplicationMode.MANUAL:
                self._update_mode(ApplicationMode.MANUAL)
            elif command == ApplicationMode.AUTO:
                self._update_mode(ApplicationMode.AUTO)
            else:
                logging.info("bad command")

        except NoNodeError:
            output = 'Could not find global mode node.'
            logging.error(output)
            self.write(output)

    def _update_mode(self, mode):
        logging.info('Updating Zookeeper global mode to {0}'.format(mode))
        data = {"mode": mode}
        self.zk.set(self.configuration.global_mode_path, json.dumps(data))
        self.write('Node successfully updated.')
        logging.info('Updated Zookeeper global mode to {0}'.format(mode))
