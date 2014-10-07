import logging
from collections import deque
from spot.zoom.agent.sentinel.common.task import Task


class UniqueQueue(deque):
    def __init__(self):
        deque.__init__(self)
        self._log = logging.getLogger('sent.q')

    def append_unique(self, task, sender='', first=False):
        """
        :type task: spot.zoom.agent.sentinel.common.task.Task
        :type sender: str
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
                self._log.info('{0} Adding "{1}" to the head of the queue.'
                               .format(sender, task.name))
                self.appendleft(task)
            else:
                self._log.info('{0} Adding "{1}" to the tail of the queue.'
                               .format(sender, task.name))
                self.append(task)
