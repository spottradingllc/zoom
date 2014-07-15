import logging
from collections import deque
from source.common.task import Task


class UniqueQueue(deque):
    def __init__(self):
        deque.__init__(self)
        self._log = logging.getLogger('sent.q')

    def append_unique(self, task, first=False):
        """
        :type task: source.common.task.Task
        :type first: bool
        """
        if not isinstance(task, Task):
            self._log.error('Queue items must be of type Task.')
            return

        if task in self:
            self._log.info('Object {0} already in queue. Not adding again.'
                           .format(task))
        else:
            if first:
                self._log.info('Adding "{0}" to the head of the queue.'
                               .format(task.name))
                self.appendleft(task)
            else:
                self._log.info('Adding "{0}" to the tail of the queue.'
                               .format(task.name))
                self.append(task)
