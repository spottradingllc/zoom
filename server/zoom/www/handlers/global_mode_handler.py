import json
import logging
import httplib
import tornado.web
import tornado.httpclient

from kazoo.exceptions import NoNodeError

from zoom.agent.entities.thread_safe_object import ApplicationMode
from zoom.common.decorators import TimeThis


class GlobalModeHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @property
    def global_mode_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.global_mode_path

    @property
    def data_store(self):
        """
        :rtype: zoom.www.cache.data_store.DataStore
        """
        return self.application.data_store

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/v1/mode/ Get global mode
        @apiVersion 1.0.0
        @apiName GetMode
        @apiGroup Mode
        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "operation_type": null,
                "global_mode": "{\"mode\":\"manual\"}",
                "update_type": "global_mode"
            }
        """
        try:
            message = self.data_store.get_global_mode()

            self.write(message.to_json())

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

        self.set_header('Content-Type', 'application/json')

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/v1/mode/ Set global Mode
        @apiParam {String} command What to set the mode to (auto|manual)
        @apiParam {String} user The user that submitted the task
        @apiVersion 1.0.0
        @apiName SetMode
        @apiGroup Mode
        """
        try:
            # parse JSON dictionary from POST
            command = self.get_argument("command")
            user = self.get_argument("user")

            logging.info("Received {0} config for Zookeeper from user {1}:{2}"
                         .format(command, user, self.request.remote_ip))

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
        self.zk.set(self.global_mode_path, json.dumps(data))
        self.write('Node successfully updated.')
        logging.info('Updated Zookeeper global mode to {0}'.format(mode))
