import json
import tornado.web

from spot.zoom.agent.sentinel.common.task import Task


class BaseHandler(tornado.web.RequestHandler):

    @property
    def log(self):
        return self.application.log

    @property
    def settings(self):
        return self.application.settings

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
            process = child['process']
            process.add_work(Task(work, block=True, pipe=True), immediate=True)
            result = process.parent_conn.recv()  # will block until done
            # synthetically create result dictionary
            # it's not directly available yet
            return {'target': target, 'work': work, 'result': result}


class WorkHandler(BaseHandler):

    def post(self, work=None, target=None):
        """
        :type work: str
        :param target: str
        """
        if work in self.settings.get('ALLOWED_WORK'):
            if target is not None:
                result = self._send_work_single(work, target)
                self.write(json.dumps(result))
            else:
                result = self._send_work_all(work)
                self.write(json.dumps(result))
        else:
            err = 'Invalid work submitted: {0}'.format(work)
            self.set_status(404, err)
            self.log.warning(err)
            self.write(json.dumps(
                {'target': target, 'work': work, 'result': '404: Not Found'})
            )


class LogHandler(BaseHandler):

    def post(self):
        data = self.application.get_log()
        self.write('\n'.join(data))

    def get(self):
        self.render('templates/log.html', data=self.application.get_log())
