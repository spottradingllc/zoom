import logging
import socket

from kazoo.exceptions import NoNodeError

from zoom.agent.entities.task import Task
from zoom.common.types import ApplicationState, CommandType
from zoom.common.decorators import connected
from zoom.common.constants import SENTINEL_METHODS


class TaskClient(object):
    def __init__(self, children, zkclient, path):
        """
        :type children: dict
        :type zkclient: kazoo.client.KazooClient
        :type path: str or None
        """
        self._log = logging.getLogger('sent.task_client')
        self._children = children
        self.zkclient = zkclient
        self._host = socket.getfqdn()
        if path is None:
            self._log.warning('Was given no path. This sentinel will not be '
                              'able to receive commands from Zoom.')
            return

        self._path = '/'.join([path, self._host])

        self.reset_watches()

    @connected
    def on_exist(self, event=None):
        try:
            if self.zkclient.exists(self._path, watch=self.on_exist):
                data, stat = self.zkclient.get(self._path)
                task = Task.from_json(data)
                self._log.info('Found work to do: {0}'.format(task))
                if task.result == ApplicationState.OK:
                    self._log.info('Task is already complete: {0}'.format(task))
                    return  # ignore tasks that are already done

                if task.name in SENTINEL_METHODS:
                    if task.target is not None:
                        self._send_work_single(task)
                    else:
                        self._send_work_all(task)
                    self._log.info("Submitted task {0} for {1}"
                                   .format(task.name, task.target))
                else:
                    err = 'Invalid work submitted: {0}'.format(task.name)
                    self._log.warning(err)

                task.result = ApplicationState.OK
                self._log.info(task.to_json())
                self.zkclient.set(self._path, task.to_json())

        except NoNodeError:
            self._log.debug('No Node at {0}'.format(self._path))

    def reset_watches(self):
        self.on_exist()

    def _send_work_all(self, task):
        """
        Send work to all children.
        :type task: zoom.agent.entities.task.Task
        :rtype: list
        """
        result = list()
        for child in self._children.keys():
            task.target = child
            result.append(self._send_work_single(task))
            return result

    def _send_work_single(self, task):
        """
        Send work to targeted child.
        :type task: zoom.agent.entities.task.Task
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
                result = '?'
                try:
                    process.add_work(task, immediate=False)
                except EOFError:
                    self._log.warning('There is nothing left to receive from '
                                      'the work manager and the other end of '
                                      'the Pipe is closed.')
                finally:
                    return {'target': task.target, 'work': task.name,
                            'result': result}