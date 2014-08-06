import logging
import json
import time
import requests
import tornado.web
from kazoo.retry import KazooRetry
from zoom.utils.decorators import timethis
from zoom.entities.types import CommandType


class ControlAgentHandler(tornado.web.RequestHandler):

    @timethis(__file__)
    def post(self):
        # parse JSON dictionary from POST
        try:
            self.component_id = self.get_argument("componentId")
            application_host = self.get_argument("applicationHost")
            self.command = self.get_argument("command")
            self.argument = self.get_argument("argument")
            user = self.get_argument("user")
    
            logging.info("Received {0} command from user '{1}' for host '{2}' for "
                         "ID '{3}'"
                         .format(self.command, user, application_host, self.component_id))
    
            self.path = self.application.configuration.task_path + application_host

            retry = KazooRetry()
            if self.command == CommandType.CANCEL:
                logging.info("removing zk path {}".format(self.path))
                retry(self.application.zk.delete, self.path)
            else:
                logging.info("attempting to add work {} on path {}".format(self.command, self.path))
                self.add_command(None)


        except Exception as e:
            logging.exception(e)

    def add_command(self, event):
        if self.application.zk.exists(self.path) is None:
            logging.info("command {}  going to zk path {}".format(self.command, self.path))
            self.application.zk.create(self.path, json.dumps({'work':self.command, 'argument':self.argument, 'target':self.component_id}))
        else:
             self.application.zk.exists(self.path, watch=self.add_command)
        
