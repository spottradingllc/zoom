import logging
from collections import deque

from zoom.agent.task.task import Task


class UniqueQueue(deque):
    def __init__(self):
        deque.__init__(self)
        self._log = logging.getLogger('sent.q')

    def append_unique(self, task, sender='', first=False):
        """
        :type task: zoom.agent.task.task.Task
        :type sender: str
        :type first: bool
        :rtype: bool
        """
        if not isinstance(task, Task):
            self._log.error('Queue items must be of type Task.')
            return False

        if task in self:
            self._log.info('Object {0} already in queue. Not adding again.'
                           .format(task))
            return False
        else:
            if first:
                self._log.info('{0} Adding "{1}" to the head of the queue.'
                               .format(sender, task.name))
                self.appendleft(task)
            else:
                self._log.info('{0} Adding "{1}" to the tail of the queue.'
                               .format(sender, task.name))
                self.append(task)
            return True
