import json
from tornado.web import RequestHandler
from zoom.agent.entities.task import Task


class BaseHandler(RequestHandler):
    @property
    def log(self):
        return self.application.log

    def _get_log(self, count=100):
        """
        :rtype: list of str
        """
        logfile = 'logs/sentinel.log'
        with open(logfile, 'r') as f:
            lines = f.readlines()
            # return last `count` rows
            return [l.rstrip('\n') for l in lines[-count:]]

    def _send_work_all(self, work):
        """
        :type work: str
        :rtype: list
        """
        result = list()
        for child in self.application.children.keys():
            result.append(self._send_work_single(work, child))
        return result

    def _send_work_single(self, work, target):
        """
        :type work: str
        :type target: str
        :rtype: dict
        """
        child = self.application.children.get(target, None)
        if child is None:
            self.log.warning('The targeted child "{0}" does not exists.'
                             .format(target))
            return {'target': target, 'work': work, 'result': '404: Not Found'}
        else:
            result = '?'
            try:
                process = child['process']
                process.add_work(Task(work, block=True, retval=True),
                                 immediate=True)
            except EOFError:
                self.log.warning('There is nothing left to receive from the '
                                 'work manager and the other end of the Pipe '
                                 'is closed.')
            finally:
                return {'target': target, 'work': work, 'result': result}


class TaskHandler(BaseHandler):
    def post(self, work=None, target=None):
        """
        @api {post} /api/v1/:work[/:target] Submit a task to Sentinel
        @apiDescription You can use this to mimic the tasks sent from Zoom.
        For example: /api/v1/stop/foo will stop the application foo.
        @apiVersion 1.0.0
        @apiName SubmitTask
        @apiGroup Sentinel Agent
        """
        if target is not None:
            result = self._send_work_single(work, target)
            self.write(json.dumps(result))
        else:
            result = self._send_work_all(work)
            self.write(json.dumps(result))


class LogHandler(BaseHandler):
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
        data = self._get_log(count=count)
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
        print count
        if count is None:
            count = 100
        else:
            count = int(count.lstrip('/'))
        self.render('../templates/log.html',
                    data=self._get_log(count=count))


class StatusHandler(BaseHandler):
    def get(self, target=None):
        """
        @api {get} /api/v1/status[/:target] Log out and retrieve status of components (html)
        @apiDescription This will retrieve the status of all the Sentinel objections
        (Components, Actions, Predicates). The GET is best used from a browser.
        @apiVersion 1.0.0
        @apiName WebGetStatus
        @apiGroup Sentinel Agent
        """
        if target is not None:
            self._send_work_single('status', target)
        else:
            result = self._send_work_all('status')
            self.write(json.dumps(result))

        line_count = 50 * len(self.application.children.keys())
        self.render('../templates/log.html',
                    data=self._get_log(count=line_count))

    def post(self, target=None):
        """
        @api {post} /api/v1/status[/:target] Log out and retrieve status of components (plaintext)
        @apiDescription This will retrieve the status of all the Sentinel objections
        (Components, Actions, Predicates). The POST is best used from curl.
        @apiVersion 1.0.0
        @apiName CurlGetStatus
        @apiGroup Sentinel Agent
        """
        if target is not None:
            self._send_work_single('status', target)
        else:
            result = self._send_work_all('status')
            self.write(json.dumps(result))

        line_count = 50 * len(self.application.children.keys())
        data = self._get_log(count=line_count)
        self.write('\n'.join(data))
