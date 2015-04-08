import logging

from zoom.agent.entities.task import Task
from zoom.agent.entities.unique_queue import UniqueQueue
from zoom.common.decorators import connected_with_return
from kazoo.exceptions import NoNodeError
from kazoo.retry import KazooRetry
from zoom.agent.util.helpers import zk_path_join


class TaskServer(object):
    def __init__(self, config, zookeeper):
        """
        :type config: zoom.config.configuration.Configuration
        :type zookeeper: zoom.www.zoo_keeper.ZooKeeper
        """
        self._configuration = config
        self._zoo_keeper = zookeeper
        self._task_queue = dict()
        # on initialization, the server will clear all tasks
        self.clear_all_tasks()

    def add_task(self, task):
        """
        Add Task to UniqueQueue. Submit task node to ZooKeeper.
        :type task: zoom.agent.entities.task.Task
        """
        if task.host not in self._task_queue:
            self._task_queue[task.host] = UniqueQueue()

        host_q = self._task_queue.get(task.host)
        host_q.append_unique(task, sender=task.host)
        self._submit_task(task)

    @connected_with_return(None)
    def clear_all_tasks(self):
        self._task_queue.clear()
        children = self._zoo_keeper.get_children(self._configuration.task_path)
        for c in children:
            path = zk_path_join(self._configuration.task_path, c)
            logging.info('Deleting stale task node {0}'.format(path))
            self._zoo_keeper.delete(path)

    def _submit_task(self, task):
        """
        If node does not exist in ZK, create node. Set data watch on that node.
        :type task: zoom.agent.entities.task.Task
        """
        try:
            task_path = zk_path_join(self._configuration.task_path, task.host)

            if self._zoo_keeper.exists(task_path):
                # if the node exists, the callback _on_update will submit the
                # next task.
                logging.info("{0} already exists. Waiting to submit task: {0}"
                             .format(task))
            else:
                logging.info("Creating task node for path {0}: {1}"
                             .format(task_path, task))
                self._zoo_keeper.create(task_path, value=task.to_json())
                self._zoo_keeper.get(task_path, watch=self._on_update)

        except NoNodeError:
            pass

    def _on_update(self, event):
        """
        Callback for the data watch on the task node
        :type event: kazoo.protocol.states.WatchedEvent
        """
        try:
            data, stat = self._zoo_keeper.get(event.path)
            task = Task.from_json(data)
            if task.result is not None:
                self._remove(task, event.path)
                self._submit_next(task.host)

            else:
                logging.info('Task result is {0}. Resetting watch'
                             .format(task.result))
                self._zoo_keeper.get(event.path, watch=self._on_update)

        except NoNodeError:
            pass

    def _remove(self, task, path, clear_queue=False):
        """
        Remove from self._task_queue. Delete node in ZooKeeper.
        :type task: zoom.agent.entities.task.Task
        :type path: str
        :type clear_queue: bool
        """
        try:
            logging.debug('Removing Task from queue: {0}'.format(task))
            host_q = self._task_queue.get(task.host, None)
            if host_q is not None:
                if clear_queue:
                    host_q.clear()
                else:
                    try:
                        # if Task is the the queue, remove it.
                        host_q.remove(task)
                    except ValueError:
                        pass

            retry = KazooRetry()
            retry(self._zoo_keeper.delete, path)
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
