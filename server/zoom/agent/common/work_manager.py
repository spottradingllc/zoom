import logging
import pprint
import time
from threading import Thread

from zoom.agent.common.thread_safe_object import ThreadSafeObject


class WorkManager(object):
    def __init__(self, comp_name, queue, pipe, work_dict):
        """
        :type comp_name: str
        :type pipe: multiprocessing.Connection
        :type queue: zoom.agent.common.unique_queue.UniqueQueue
        :type work_dict: dict
        """
        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run,
                              name='work_manager',
                              args=(self._operate, queue, pipe, work_dict))
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

    def _run(self, operate, queue, pipe, work_dict):
        while operate == True:
            if queue:  # if queue is not empty
                self._log.info('Current Task Queue:\n{0}'
                               .format(pprint.pformat(list(queue))))
                task = queue[0]  # grab task, but keep it in the queue

                if task.func is None:
                    func_to_run = work_dict.get(task.name, None)
                else:
                    func_to_run = task.func

                if func_to_run is not None:
                    self._log.info('Found work "{0}" in queue.'
                                   .format(task.name))
                    t = Thread(target=func_to_run, name=task.name,
                               args=task.args, kwargs=task.kwargs)
                    t.start()
                    # the block should come before the pipe if we want to
                    # capture the result and send it off
                    if task.pipe:
                        pipe.send('OK')

                    if task.block:
                        t.join()
                else:
                    if task.pipe:
                        pipe.send('')
                    self._log.warning('Cannot do "{0}", it is not a valid '
                                      'action.'.format(task.name))
                try:
                    queue.remove(task)
                except ValueError:
                    self._log.debug('Item no longer exists in the queue: {0}'
                                    .format(task))
            else:
                time.sleep(1)

        self._log.info('Done listening for work.')
        return
