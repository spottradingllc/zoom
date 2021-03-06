import logging
from threading import Thread

from zoom.common.types import ApplicationType
from zoom.agent.entities.application import Application
from zoom.agent.entities.job import Job
from zoom.agent.task.task import Task
from zoom.agent.entities.thread_safe_object import ThreadSafeObject
from zoom.agent.entities.unique_queue import UniqueQueue
from zoom.agent.util.helpers import verify_attribute


class ChildProcess(object):
    """
    Wraps a threading.Thread, providing a Queue for communication between
    the SentinelDaemon and the ChildProcess.
    """
    def __init__(self, config, system, settings):
        """
        :type config: xml.etree.ElementTree.Element
        :type system: zoom.common.types.PlatformType
        :type settings: dict
        """
        self._log = logging.getLogger('sent.child')
        self._action_queue = UniqueQueue()
        self._cancel_flag = ThreadSafeObject(False)

        self.name = verify_attribute(config, 'id')
        self._application_type = verify_attribute(config, 'type')
        self._config = config
        self._system = system  # Linux or Windows
        self._settings = settings
        self._process = self._create_process()

    def add_work(self, work, immediate=False):
        """
        :type work: zoom.agent.task.task.Task
        :type immediate: bool
        :rtype: bool
        """
        return self._action_queue.append_unique(work,
                                                sender=str(self),
                                                first=immediate)

    def cancel_current_task(self):
        """
        Set the cancel flag that is used in the process client.
        """
        # this seems like a hack. There must be a better way of cancelling while
        #   still allowing the agent to report up/down status
        DONT_REMOVE = ('register', 'unregister')
        self._log.info('Setting Cancel Flag and clearing queue.')
        self._cancel_flag.set_value(True)
        for i in list(self._action_queue):
            if i.name not in DONT_REMOVE:
                self._action_queue.remove(i)
                self._log.info('Removing task {0}'.format(i))

    def stop(self):
        """
        Stops the Process/Thread
        """ 
        try:
            self._log.info('Terminating {0} child process'.format(self.name))
            self.cancel_current_task()
            self.add_work(Task('terminate', block=True), immediate=True)
        except Exception as e:
            self._log.warning('Exception with stopping {0} child process: {1}'
                              .format(self.name, e))

    def join(self):
        """
        Block until underlying process completes.
        """
        self._process.join()
        self._log.info('{0} stopped.'.format(self))

    def _create_process(self):
        """
        :rtype: threading.Thread
        """
        self._log.debug('Starting worker process for %s' % self.name)
        
        if self._application_type == ApplicationType.APPLICATION:
            s = Application(self._config, self._settings, self._action_queue,
                            self._system, self._application_type,
                            self._cancel_flag)
        elif self._application_type == ApplicationType.JOB:
            s = Job(self._config, self._settings, self._action_queue,
                    self._system, self._application_type, self._cancel_flag)
            
        t = Thread(target=s.run, name=self.name)
        t.daemon = True
        t.start()
        return t
    
    def __str__(self):
        return 'ChildProcess(name={0}, type={1})'.format(self.name,
                                                         self._application_type)
