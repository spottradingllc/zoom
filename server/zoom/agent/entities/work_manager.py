import logging
import pprint
import time
from threading import Thread

from zoom.agent.entities.thread_safe_object import ThreadSafeObject


class ThreadWithReturn(Thread):
    def __init__(self, *args, **kwargs):
        super(ThreadWithReturn, self).__init__(*args, **kwargs)

        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)

    def join(self, *args, **kwargs):
        super(ThreadWithReturn, self).join(*args, **kwargs)

        return self._return


class WorkManager(object):
    def __init__(self, comp_name, queue, work_dict):
        """
        :type comp_name: str
        :type pipe: multiprocessing.Connection
        :type queue: zoom.agent.entities.unique_queue.UniqueQueue
        :type work_dict: dict
        """
        self._operate = ThreadSafeObject(True)
        self._thread = Thread(target=self._run,
                              name='work_manager',
                              args=(self._operate, queue, work_dict))
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

    def _run(self, operate, queue, work_dict):
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
                    retval = None
                    t = ThreadWithReturn(target=func_to_run, name=task.name,
                                         args=task.args, kwargs=task.kwargs)
                    t.start()

                    if task.block:
                        retval = t.join()

                else:
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