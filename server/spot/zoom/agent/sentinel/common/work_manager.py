import logging
import time
from threading import Thread

from spot.zoom.agent.sentinel.common.enum import SimpleObject


class WorkManager(object):
    def __init__(self, comp_name, queue, pipe, tasks):
        """
        :type comp_name: str
        :type pipe: multiprocessing.Connection
        :type queue: sentinel.common.unique_queue.UniqueQueue
        :type tasks: dict
        """
        self._operate = SimpleObject(True)
        self._thread = Thread(target=self._run,
                              name='work_manager',
                              args=(self._operate, queue, pipe, tasks))
        self._thread.daemon = True
        self._log = logging.getLogger('sent.{0}.wm'.format(comp_name))

    def start(self):
        self._log.info('starting work manager')
        self._thread.start()

    def stop(self):
        self._log.info('Stopping work manager.')
        self._operate.set_value(False)
        self._thread.join()
        self._log.info('Stopped work manager.')

    def _run(self, operate, queue, pipe, tasks):
        while operate == True:
            if queue:  # if queue is not empty

                item = queue.popleft()
                if item.func is None:
                    task = tasks.get(item.name, None)
                else:
                    task = item.func

                if task is not None:
                    self._log.info('Found work "%s" in queue.' % item.name)
                    t = Thread(target=task, name=item.name,
                               args=item.args, kwargs=item.kwargs)
                    t.start()
                    # the block should come before the pipe if we want to
                    # capture the result and send it off
                    if item.pipe:
                        pipe.send('OK')
                    if item.block:
                        t.join()
                else:
                    if item.pipe:
                        pipe.send('')
                    self._log.warning('Cannot do "%s", it is not allowed.'
                                      % item.name)
            else:
                time.sleep(1)

        self._log.info('Done listening for work.')
        return