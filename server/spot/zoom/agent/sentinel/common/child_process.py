import logging
from multiprocessing import Pipe
from threading import Thread

from spot.zoom.common.types import ApplicationType
from spot.zoom.agent.sentinel.common.application import Application
from spot.zoom.agent.sentinel.common.job import Job
from spot.zoom.agent.sentinel.common.task import Task
from spot.zoom.agent.sentinel.common.unique_queue import UniqueQueue
from spot.zoom.agent.sentinel.util.helpers import verify_attribute


class ChildProcess(object):
    """
    Wraps a multiprocess.Process instance, providing a Pipe and a Queue for
    communication between the SentinelDaemon and the ChildProcess.
    """
    def __init__(self, config, system, settings):
        """
        :type config: xml.etree.ElementTree.Element
        :type system: spot.zoom.common.types.PlatformType
        """
        self._log = logging.getLogger('sent.child')
        self.parent_conn, self.child_conn = Pipe()
        self._action_queue = UniqueQueue()

        self.name = verify_attribute(config, 'id')
        self._application_type = verify_attribute(config, 'type')
        self._config = config
        self._system = system  # Linux or Windows
        self._settings = settings
        self._process = self._create_process()

    def add_work(self, work, immediate=False):
        """
        :type work: spot.zoom.agent.sentinel.common.task.Task
        """
        self._action_queue.append_unique(work, sender=str(self),
                                         first=immediate)

    def stop(self):
        """
        Stops the Process/Thread
        """ 
        try:
            self._log.info('Terminating {0} child process'.format(self.name))

            self.add_work(Task('terminate', block=True), immediate=True)
            self._process.join()
            self._log.info('{0} stopped.'.format(self))
        except Exception as e:
            self._log.warning('Exception with stopping {0} child process: {1}'
                              .format(self.name, e))

    def _create_process(self):
        """
        :rtype: threading.Thread
        """
        self._log.debug('Starting worker process for %s' % self.name)
        
        if self._application_type == ApplicationType.APPLICATION:
            s = Application(self._config, self._settings, self.child_conn,
                            self._action_queue, self._system,
                            self._application_type)
        elif self._application_type == ApplicationType.JOB:
            s = Job(self._config, self._settings, self.child_conn,
                    self._action_queue, self._system, self._application_type)
            
        t = Thread(target=s.run, name=self.name)
        t.daemon = True
        t.start()
        return t
    
    def __str__(self):
        return 'ChildProcess(name={0}, type={1})'.format(self.name,
                                                         self._application_type)
