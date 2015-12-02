import logging
import socket
import time
from zoom.common.types import CommandType


class BaseTaskClient(object):
    def __init__(self, children):
        """
        :type children: dict
        """
        self._log = logging.getLogger('sent.task_client')
        self._children = children
        self._host = socket.getfqdn()

    def send_work_all(self, task, wait=False, immediate=False):
        """
        Send work to all children.
        :type task: zoom.agent.task.Task
        :type wait: bool
        :param wait: Whether to wait for the function to finish before exiting
        :type immediate: bool
        :param immediate: Whether to put the task at the head of the queue

        :rtype: dict
        """
        result = dict()
        for child in self._children.keys():
            task.target = child
            result[child] = self.send_work_single(task,
                                                  wait=wait,
                                                  immediate=immediate)

        return result

    def send_work_single(self, task, wait=False, immediate=False, timeout=None):
        """
        Send work to targeted child.
        :type task: zoom.agent.task.task.Task
        :type wait: bool
        :param wait: Whether to wait for the function to finish before exiting
        :type immediate: bool
        :param immediate: Whether to put the task at the head of the queue
        :type timeout: int or None
        :rtype: dict
        """
        child = self._children.get(task.target, None)
        if child is None:
            self._log.warning('The targeted child "{0}" does not exists.'
                              .format(task.target))
            return {'target': task.target, 'work': task.name,
                    'result': '404: Not Found'}

        else:
            process = child['process']
            if task.name == CommandType.CANCEL:
                process.cancel_current_task()
                return {'target': task.target, 'work': task.name,
                        'result': CommandType.CANCEL}
            else:
                process.add_work(task, immediate=immediate)

                wait_time = 0
                if wait:
                    while task.result is None:
                        time.sleep(1)
                        if timeout is not None:
                            wait_time += 1
                            if wait_time > timeout:
                                break

            return {'target': task.target, 'work': task.name,
                    'result': task.result}
