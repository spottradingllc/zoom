import logging
import platform
import time

from kazoo.exceptions import NoNodeError

from spot.zoom.agent.sentinel.common.task import Task
from spot.zoom.common.types import ApplicationState
from spot.zoom.common.decorators import (
    connected,
)


class TaskClient(object):
    def __init__(self, children, zkclient, settings):
        """
        :type children: dict
        :type zkclient: kazoo.client.KazooClient
        :type settings: dict
        """
        self._log = logging.getLogger('sent.task_client')
        self._children = children
        self._zkclient = zkclient
        self._settings = settings
        self._host = platform.node()

        # this is to handle a race condition
        while not settings.get('ZK_TASK_PATH'):
            self._log.info('Waiting for settings.')
            time.sleep(1)

        task_path = settings.get('ZK_TASK_PATH')
        self._path = '/'.join([task_path, self._host])

        self.reset_watches()

    @connected
    def on_exist(self, event=None):
        try:
            if self._zkclient.exists(self._path, watch=self.on_exist):
                self._log.info('Found work to do.')
                data, stat = self._zkclient.get(self._path)
                task = Task.from_json(data)
                if task.result == ApplicationState.OK:
                    return  # ignore tasks that are already done

                if task.name in self._settings.get('ALLOWED_WORK'):
                    if task.target is not None:
                        self._send_work_single(task)
                    else:
                        self._send_work_all(task)
                    self._log.info("just {0}'d {1}".format(task.name, task.target))
                else:
                    err = 'Invalid work submitted: {0}'.format(task.name)
                    self._log.warning(err)

                task.result = ApplicationState.OK
                self._log.info(task.to_json())
                self._zkclient.set(self._path, task.to_json())

        except NoNodeError:
            self._log.debug('No Node at {0}'.format(self._path))

    def reset_watches(self):
        self.on_exist()

    def _send_work_all(self, task):
        """
        Send work to all children.
        :type task: spot.zoom.agent.sentinel.common.task.Task
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
        :type task: spot.zoom.agent.sentinel.common.task.Task
        """
        child = self._children.get(task.target, None)
        if child is None:
            self._log.warning('The targeted child "{0}" does not exists.'
                              .format(task.target))
            return {
                'target': task.target,
                'work': task.name,
                'result': '404: Not Found'
            }

        else:
            process = child['process']
            process.add_work(task, immediate=False)
            result = process.parent_conn.recv()  # will block until done
            return {'target': task.target, 'work': task.name, 'result': result}