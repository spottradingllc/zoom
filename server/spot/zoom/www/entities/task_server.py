import os.path
import logging
from spot.zoom.agent.sentinel.common.task import Task
from spot.zoom.agent.sentinel.common.unique_queue import UniqueQueue
from spot.zoom.common.types import ApplicationState
from kazoo.exceptions import NoNodeError
from spot.zoom.common.types import CommandType
from kazoo.retry import KazooRetry


class TaskServer(object):
    def __init__(self, config, zookeeper):
        """
        :type config: spot.zoom.config.configuration.Configuration
        :type zookeeper: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        self._configuration = config
        self._zookeeper = zookeeper
        self._task_queue = dict()
        # on initialization, the server will clear all tasks
        self.clear_all_tasks()

    def add_task(self, task):
        """
        Add Task to UniqueQueue. Submit task node to ZooKeeper.
        :type task: spot.zoom.agent.sentinel.common.task.Task
        """
        if task.host not in self._task_queue:
            self._task_queue[task.host] = UniqueQueue()

        host_q = self._task_queue.get(task.host)
        host_q.append_unique(task, sender=task.host)
        self._submit_task(task)

    def clear_all_tasks(self):
        self._task_queue.clear()
        children = self._zookeeper.get_children(self._configuration.task_path)
        for c in children:
            path = os.path.join(self._configuration.task_path, c)
            logging.info('Deleting stale task node {0}'.format(path))
            self._zookeeper.delete(path)

    def _submit_task(self, task):
        """
        If node does not exist in ZK, create node. Set data watch on that node.
        :type task: spot.zoom.agent.sentinel.common.task.Task
        """
        try:
            task_path = os.path.join(self._configuration.task_path, task.host)

            if self._zookeeper.exists(task_path):
                if task.name == CommandType.CANCEL:
                    # TODO: do we really want to delete the node on CANCEL?
                    self._remove(task, task_path, clear_queue=True)

                else:
                    # if the node exists, the callback _on_update will submit the
                    # next task.
                    logging.info("Task path {0} already exists. Waiting to "
                                 "submit task: {0}".format(task))
            else:
                logging.info("Creating task node for path {0}: {1}"
                             .format(task_path, task))
                self._zookeeper.create(task_path, value=task.to_json())
                self._zookeeper.get(task_path, watch=self._on_update)

        except NoNodeError:
            pass

    def _on_update(self, event):
        """
        Callback for the data watch on the task node
        :type event: kazoo.protocol.states.WatchedEvent
        """
        try:
            data, stat = self._zookeeper.get(event.path)
            task = Task.from_json(data)
            if task.result == ApplicationState.OK:
                self._remove(task, event.path)
                self._submit_next(task.host)

            else:
                logging.info('Task result is {0}. Resetting watch'
                             .format(task.result))
                self._zookeeper.get(event.path, watch=self._on_update)

        except NoNodeError:
            pass

    def _remove(self, task, path, clear_queue=False):
        """
        Remove from self._task_queue. Delete node in ZooKeeper.
        :type task: spot.zoom.agent.sentinel.common.task.Task
        """
        try:
            host_q = self._task_queue.get(task.host, None)
            if host_q is not None:
                if clear_queue:
                    host_q.clear()
                else:
                    host_q.remove(task)

            retry = KazooRetry()
            retry(self._zookeeper.delete, path)

        except NoNodeError:
            pass

    def _submit_next(self, host):
        """
        Submit next task from the queue (if there is one)
        :type host: str
        """
        host_q = self._task_queue.get(host, None)
        if host_q:
            next_task = host_q[0]
            self._submit_task(next_task)
