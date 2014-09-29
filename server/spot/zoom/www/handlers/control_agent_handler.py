import logging
import json
import os

from httplib import INTERNAL_SERVER_ERROR

import tornado.web

from kazoo.retry import KazooRetry

from spot.zoom.www.utils.decorators import TimeThis
from spot.zoom.common.types import CommandType


class ControlAgentHandler(tornado.web.RequestHandler):

    @TimeThis(__file__)
    def post(self):
        try:
            self.component_id = self.get_argument("componentId")
            application_host = self.get_argument("applicationHost")
            self.command = self.get_argument("command")
            self.argument = self.get_argument("argument")
            user = self.get_argument("user")
    
            logging.info("Received {0} command from user '{1}' for host '{2}' "
                         "for ID '{3}'"
                         .format(self.command, user, application_host,
                                 self.component_id))
    
            self.path = os.path.join(self.application.configuration.task_path,
                                     application_host)

            retry = KazooRetry()
            if self.command == CommandType.CANCEL:
                logging.info("removing zk path {0}".format(self.path))
                retry(self.application.zk.delete, self.path)
            else:
                logging.info("attempting to add work {0} on path {1}"
                             .format(self.command, self.path))
                self.add_command()

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

    def add_command(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent
        """
        # TODO find a better way to pass parameters here
        if self.application.zk.exists(self.path) is None:
            logging.info("command {0} with argument {1} going to zk path {2}"
                         .format(self.command, self.argument, self.path))
            self.application.zk.create(self.path, json.dumps(
                {'work': self.command, 'argument': self.argument,
                 'target': self.component_id}))
        else:
            self.application.zk.exists(self.path, watch=self.add_command)
