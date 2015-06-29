import json
import logging
import tornado.web

from zoom.agent.entities.task import Task


class BaseHandler(tornado.web.RequestHandler):

    @property
    def log(self):
        return self.application.log

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
                process.add_work(Task(work, block=True, pipe=True, retval=True),
                                 immediate=True)
                result = process.parent_conn.recv()  # will block until done
                # synthetically create result dictionary
                # it's not directly available yet
            except EOFError:
                self.log.warning('There is nothing left to receive from the '
                                 'work manager and the other end of the Pipe '
                                 'is closed.')
            finally:
                return {'target': target, 'work': work, 'result': result}


class WorkHandler(BaseHandler):

    def post(self, work=None, target=None):
        """
        :type work: str
        :param target: str
        """
        if target is not None:
            result = self._send_work_single(work, target)
            self.write(json.dumps(result))
        else:
            result = self._send_work_all(work)
            self.write(json.dumps(result))


class LogHandler(BaseHandler):

    def post(self):
        data = self.application.get_log()
        self.write('\n'.join(data))

    def get(self):
        self.render('templates/log.html', data=self.application.get_log())


class LogVerbosityHandler(BaseHandler):

    def post(self, level):
        logger = logging.getLogger('')
        level = level.lower()
        if level == 'debug':
            logger.setLevel(logging.DEBUG)
        elif level == 'info':
            logger.setLevel(logging.INFO)
        elif level == 'warning':
            logger.setLevel(logging.WARNING)
        else:
            return

        logging.info('Changed log level to {0}'.format(level))
