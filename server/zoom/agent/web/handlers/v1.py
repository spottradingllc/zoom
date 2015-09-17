import json
from tornado.web import RequestHandler
from zoom.agent.task.task import Task
from zoom.agent.util.helpers import get_log


class TaskHandler(RequestHandler):
    def post(self, work=None, target=None):
        """
        @api {post} /api/v1/:work[/:target] Submit a task to Sentinel
        @apiDescription You can use this to mimic the tasks sent from Zoom.
        For example: /api/v1/stop/foo will stop the application foo.
        @apiVersion 1.0.0
        @apiName SubmitTask
        @apiGroup Sentinel Agent
        """
        tc = self.application.task_client
        task = Task(work, target=target, block=True, retval=True)

        if target is not None:
            result = tc.send_work_single(task, immediate=True)
            self.write(json.dumps(result))
        else:
            result = tc.send_work_all(task, immediate=True)

        self.write(json.dumps(result))


class LogHandler(RequestHandler):
    def post(self, count):
        """
        @api {post} /api/v1/log[/:linecount] Retrieve lines from the logfile (plaintext)
        @apiDescription This will retrieve the lines in plaintext. Best if used by curl.
        You can optionally provide the number of lines you would like to receive.
        For example: /api/v1/log/40
        @apiVersion 1.0.0
        @apiName CurlLogLines
        @apiGroup Sentinel Agent
        """
        if count is None:
            count = 100
        data = get_log(count=count)
        self.write('\n'.join(data))

    def get(self, count):
        """
        @api {get} /api/v1/log[/:linecount] Retrieve lines from the logfile (html)
        @apiDescription This will retrieve the lines in HTML. Best if used by a browser.
        You can optionally provide the number of lines you would like to receive.
        For example: /api/v1/log/40
        @apiVersion 1.0.0
        @apiName WebLogLines
        @apiGroup Sentinel Agent
        """
        if count is None:
            count = 100
        else:
            count = int(count.lstrip('/'))
        self.render('../templates/log.html',
                    data=get_log(count=count))


class StatusHandler(RequestHandler):
    def get(self, target=None):
        """
        @api {get} /api/v1/status[/:target] Log out and retrieve status of components (html)
        @apiDescription This will retrieve the status of all the Sentinel objections
        (Components, Actions, Predicates). The GET is best used from a browser.
        @apiVersion 1.0.0
        @apiName WebGetStatus
        @apiGroup Sentinel Agent
        """
        tc = self.application.task_client
        task = Task('status', target=target, block=True, retval=True)
        if target is not None:
            tc.send_work_single(task, wait=True, immediate=True)
        else:
            tc.send_work_all(task, wait=True, immediate=True)

        line_count = 50 * len(self.application.children.keys())
        self.render('../templates/log.html',
                    data=get_log(count=line_count))

    def post(self, target=None):
        """
        @api {post} /api/v1/status[/:target] Log out and retrieve status of components (plaintext)
        @apiDescription This will retrieve the status of all the Sentinel objections
        (Components, Actions, Predicates). The POST is best used from curl.
        @apiVersion 1.0.0
        @apiName CurlGetStatus
        @apiGroup Sentinel Agent
        """
        tc = self.application.task_client
        task = Task('status', target=target, block=True, retval=True)
        if target is not None:
            result = tc.send_work_single(task, wait=True, immediate=True)
            self.write(result.get('result'))
        else:
            result = tc.send_work_all(task, wait=True,  immediate=True)
            for i in result.values():
                self.write(i.get('result'))
