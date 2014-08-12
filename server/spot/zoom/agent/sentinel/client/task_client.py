import logging
import platform
import json

from sentinel.config.constants import ALLOWED_WORK
from sentinel.config.constants import ZK_TASK_PATH
from sentinel.common.task import Task

class TaskClient(object):
    def __init__(self, zkclient, children):
        self._log = logging.getLogger('sent.task_client')
        self._children = children
        self._zkclient = zkclient
        self._host = platform.node()
        self._path = '/'.join([ZK_TASK_PATH, self._host])

        self.reset_watches()

    def onExists(self, event):
        if self._zkclient.exists(self._path, self.onExists) is not None:
            jsonstr, stat = self._zkclient.get(self._path)
            data = json.loads(jsonstr)
            work = data.get('work', None)
            argument = {'argument': data.get('argument', None)}
            target = data.get('target', None)

            if work in ALLOWED_WORK:
                if target is not None:
                    result = self._send_work_single(work, target, kwargs=argument)
                else:
                    result = self._send_work_all(work, kwargs=argument)
                logging.info("just {}'d {}".format(work, target))
            else:
                err = 'Invalid work submitted: {0}'.format(work)
                self._log.warning(err)

            self._zkclient.delete(self._path)

    def reset_watches(self):
        if self._zkclient.exists(self._path, self.onExists) is not None:
            self.onExists(None)

    def _send_work_all(self, work, kwargs={}):
        """
        :type work: str
        :rtype: list
        """
        result = list()
        for child in self._children.keys():
            result.append(self._send_work_single(work, child, kwargs=kwargs))
        return result


    def _send_work_single(self, work, target, kwargs={}):
        """
        :type work: str
        :type target: str
        :rtype: dict
        """
        child = self._children.get(target, None)
        if child is None:
            self._log.warning('The targeted child "{0}" does not exists.'
                             .format(target))
            return {'target': target, 'work': work, 'result': '404: Not Found'}
        else:
            process = child['process']
            process.add_work(Task(work, kwargs=kwargs, block=True, pipe=True), immediate=True)
            result = process.parent_conn.recv()  # will block until done
            return {'target': target, 'work': work, 'result': result}
                
                
            

