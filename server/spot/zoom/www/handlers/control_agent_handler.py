import logging
import json
import tornado.web

from httplib import INTERNAL_SERVER_ERROR

from spot.zoom.common.decorators import TimeThis
from spot.zoom.agent.sentinel.common.task import Task


class ControlAgentHandler(tornado.web.RequestHandler):
    @property
    def task_server(self):
        """
        :rtype: spot.zoom.www.entities.task_server.TaskServer
        """
        return self.application.task_server
    
    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def post(self):
        """
        Create Task from json and add to TaskServer
        """
        try:
            kwarguments = {
                'stay_down': self.get_argument("stay_down", default=None),
                'login_user': self.get_argument("user", default=None),
            }
            task = Task(self.get_argument("command"),
                        target=self.get_argument("componentId"),
                        kwargs=kwarguments,
                        pipe=True,
                        host=self.get_argument("applicationHost"))

            logging.info("Received task request from client {0}: {1}"
                         .format(self.request.remote_ip, task))
            self.task_server.add_task(task)

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)
