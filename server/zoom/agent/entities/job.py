import json
from time import sleep
from datetime import datetime

from kazoo.exceptions import (
    NodeExistsError,
    NoNodeError,
    SessionExpiredError
)

from zoom.common.types import JobState
from zoom.agent.entities.application import Application
from zoom.common.decorators import (
    connected,
    time_this,
    catch_exception
)


class Job(Application):
    def __init__(self, *args, **kwargs):
        Application.__init__(self, *args, **kwargs)
        self._paths['zk_state_path'] = \
            self._pathjoin(self._paths['zk_state_base'], 'gut')

    @time_this
    def start(self, **kwargs):
        """Start actual process"""
        if kwargs.get('reset', True):
            self._proc_client.reset_counters()
        if kwargs.get('pause', False):
            self.ignore()

        self.unregister()
        self._register_job_state(JobState.RUNNING)

        start_time = datetime.now()
        retcode = self._proc_client.start()
        stop_time = datetime.now()

        if retcode == 0:
            self.register(stop_time)
            self._register_job_state(JobState.SUCCESS,
                                     runtime=str(stop_time - start_time))
        else:
            self._register_job_state(JobState.FAILURE,
                                     runtime=str(stop_time - start_time))

        return 'OK'

    @catch_exception(NodeExistsError)
    @connected
    def register(self, now):
        """
        Add entry to the state tree
        :type now: datetime.datetime
        """
        stoptime = now.replace(hour=23, minute=59, second=59, microsecond=0)
        data = {'stop': str(stoptime)}
        self._log.info('Registering %s in state tree.' % self.name)
        self.zkclient.create(self._paths['zk_state_path'],
                             value=json.dumps(data),
                             makepath=True)

    @catch_exception(NoNodeError)
    @connected
    def unregister(self):
        """Remove entry from state tree"""
        self._log.info('Un-registering %s from state tree.' % self.name)
        self.zkclient.delete(self._paths['zk_state_path'])

    def run(self):
        self.zkclient.start()
        self._check_mode()
        self._log.info('Starting to process Actions.')
        map(lambda x: x.start(), self._actions.values())  # start actions

        while self._running:
            sleep(1)

        self.uninitialize()

    @catch_exception(SessionExpiredError)
    @connected
    def _register_job_state(self, state, runtime=''):
        """
        :type state: zoom.common.types.JobState
        :param runtime: str
        """
        data = {
            'name': self.name,
            'state': state,
            'runtime': runtime
        }

        if not self.zkclient.exists(self._paths['zk_state_base']):
            self.zkclient.create(self._paths['zk_state_base'],
                                 value=json.dumps(data),
                                 makepath=True)
        else:
            self.zkclient.set(self._paths['zk_state_base'], json.dumps(data))
