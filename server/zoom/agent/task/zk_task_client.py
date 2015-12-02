from kazoo.exceptions import NoNodeError

from zoom.agent.task.task import Task
from zoom.agent.task.base_task_client import BaseTaskClient
from zoom.common.types import ApplicationState
from zoom.common.decorators import connected
from zoom.common.constants import SENTINEL_METHODS


class ZKTaskClient(BaseTaskClient):
    def __init__(self, children, zkclient, path):
        """
        :type children: dict
        :type zkclient: kazoo.client.KazooClient
        :type path: str or None
        """
        BaseTaskClient.__init__(self, children)
        self.zkclient = zkclient
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
                    self._log.debug('Task is already complete: {0}'.format(task))
                    return  # ignore tasks that are already done

                if task.name in SENTINEL_METHODS:
                    if task.target is not None:
                        self.send_work_single(task)
                    else:
                        self.send_work_all(task)
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
