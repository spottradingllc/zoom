import logging
import json
import tornado.web

from httplib import INTERNAL_SERVER_ERROR

from zoom.common.decorators import TimeThis
from zoom.common.types import CommandType
from zoom.agent.entities.task import Task


class ControlAgentHandler(tornado.web.RequestHandler):
    @property
    def task_server(self):
        """
        :rtype: zoom.www.entities.task_server.TaskServer
        """
        return self.application.task_server
    
    @property
    def zk(self):
        """
        :rtype: zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/agent/ Create Task from json and add to TaskServer
        @apiParam {Boolean} [stay_down=null] Used to signal to Sentinel that the application was brought down on purpose
        @apiParam {String} [login_user=null] The user that submitted the task
        @apiParam {String} command The function Sentinel should run
        @apiParam {String} componentId The app targeted for the task
        @apiParam {String} applicationHost The host the app is running on
        @apiVersion 1.0.0
        @apiName CreateTask
        @apiGroup Task
        """
        try:
            kwarguments = {
                'stay_down': self.get_argument("stay_down", default=None),
                'login_user': self.get_argument("user", default=None),
            }
            task = Task(self.get_argument("command"),
                        target=self.get_argument("componentId"),
                        kwargs=kwarguments,
                        host=self.get_argument("applicationHost"))

            logging.info("Received task request from client {0}: {1}"
                         .format(self.request.remote_ip, task))

            cancel = task.name == CommandType.CANCEL
            self.task_server.add_task(task, is_cancel=cancel)

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write(json.dumps({'errorText': str(e)}))
            logging.exception(e)

    @TimeThis(__file__)
    def delete(self):
        """
        @api {delete} /api/agent/ Delete all tasks in queue
        @apiVersion 1.0.0
        @apiName DeleteTasks
        @apiGroup Task
        """
        self.task_server.clear_all_tasks()

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/agent/ Get live and queued tasks
        @apiVersion 1.0.0
        @apiName GetTasks
        @apiGroup Task
        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "queued_tasks": { },
                "live_tasks": { }
            }
        """
        self.write({
            "queued_tasks": self.task_server.queued_tasks,
            "live_tasks": self.task_server.live_tasks
        })
