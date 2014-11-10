import logging
import os
import psutil
import shlex
import socket

from multiprocessing import Lock
from time import sleep, time

from spot.zoom.common.types import (
    PlatformType,
    ApplicationType,
    ApplicationStatus
)
from spot.zoom.agent.sentinel.common.restart import RestartLogic
from spot.zoom.agent.sentinel.client.graphite_client import GraphiteClient


class ProcessClient(object):
    def __init__(self, name=None, command=None, script=None, apptype=None,
                 system=None, restart_max=None, restart_on_crash=None,
                 graphite_metric_names=None, settings=None):
        """
        :type name: str or None
        :type command: str or None
        :type script: str or None
        :type apptype: spot.zoom.common.types.ApplicationType
        :type system: spot.zoom.common.types.PlatformType
        :type restart_max: int or None
        :type restart_on_crash: bool or None
        :type graphite_metric_names: dict
        :type settings: dict
        """
        assert any((name, command, script)), \
            ('Cannot initialize ProcessClient if name, command, and script'
             ' are all None.')

        self._log = logging.getLogger('sent.{0}.process'.format(name))
        self.command = command
        self.name = name
        self.process_client_lock = Lock()  # lock for synchronous decorator
        self.ran_stop = None
        self._script = script
        self._apptype = apptype
        self._system = system
        self._stay_down = False
        self.restart_logic = RestartLogic(restart_on_crash, restart_max)

        self.last_status = False
        self._graphite_metric_names = graphite_metric_names
        self._settings = settings

    @property
    def script_name(self):
        if self._script is not None:
            return self._script
        else:
            return self.name

    @property
    def start_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._job_start
        elif self._apptype == ApplicationType.APPLICATION:
            if self.command is not None:  # custom start command
                return self._job_start
            else:
                return self._service_start

    @property
    def status_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._job_status
        elif self._apptype == ApplicationType.APPLICATION:
            return self._service_status

    @property
    def stop_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._job_stop
        elif self._apptype == ApplicationType.APPLICATION:
            return self._service_stop

    @property
    def reset_counters(self):
        return self.restart_logic.reset_count

    @property
    def restart_allowed(self):
        return self.restart_logic.restart_allowed

    def running(self):
        """
        :type reset: bool
        :return: Whether the process is running.
        :rtype: bool
        """
        self.last_status = self.status_method()

        self._log.debug('Process {0} running: {1}'
                        .format(self.name, self.last_status))
        return self.last_status

    def start(self):
        """Try to start process"""
        if self._stay_down:
            self._log.info('Graceful shutdown. Not starting back up')
            return 0

        if self._apptype == ApplicationType.APPLICATION:
            self._stop_if_running()

        return_code = -1

        while not self.restart_logic.restart_max_reached:
            self.restart_logic.increment_count()

            start_time = time()
            return_code = self.start_method()
            finish_time = time()
            # send runtime and return code to graphite
            self.send_to_graphite(self._graphite_metric_names['result'],
                                  return_code)
            self.send_to_graphite(self._graphite_metric_names['runtime'],
                                  finish_time - start_time)

            if return_code == 0:
                self._log.info('{0} start successful in {1} tries.'
                               .format(self.name, self.restart_logic.count))
                self.reset_counters()
                break
            else:
                self._log.info('{0} start attempt {1} failed.'
                               .format(self.name, self.restart_logic.count))
                self._stop_if_running()
                self._log.debug('Waiting 10 seconds before trying again.')
                sleep(10)  # minor wait before we try again

        self.ran_stop = False
        return return_code

    def stop(self, **kwargs):
        """Stop process"""
        self.ran_stop = True

        if kwargs.get('stay_down', 'false') == 'true':
            self._stay_down = True
        else:
            self._stay_down = False

        return_code = self.stop_method()

        if return_code != 0:
            self._log.error('There was some issue with the stop command. '
                            'Return code was: {0}'.format(return_code))

        if self.running():
            self._log.error('App is still running after running stop!')

        return return_code

    def send_to_graphite(self, metric, data, tstamp=None, env=None):
        try:
            GraphiteClient.send(metric, data, tstamp=tstamp, env=env)
        except socket.timeout:
            self._log.error('Could not connect to Graphite')
        except IOError as e:
            self._log.error('Check shortage of file descriptor: {0}'.format(e))
        except Exception as e:
            self._log.error('Unknown exception while sending data to Graphite:'
                            ' {0}'.format(e))

    def _stop_if_running(self):
        """
        Will run stop() if the application is running.
        """
        if self.running():
            self._log.warning('The application is running. Attempting stop.')
            self.stop()
            
    def _job_start(self):
        """
        Start process by running some arbitrary command
        """
        return_code = -1
        self._log.info('Starting {0}'.format(self.command))
        if self._system == PlatformType.LINUX:
            cmd = shlex.split(self.command)
        else:
            cmd = self.command

        with open(os.devnull, 'w') as devnull:
            p = psutil.Popen(cmd, stdout=devnull, stderr=devnull)
            while True:
                return_code = p.poll()
                if return_code is not None:  # None = still running
                    break
                elif p.status == psutil.STATUS_ZOMBIE:
                    self._log.warning(
                        '{0} command resulted in a zombie process. '
                        'Returning with -1'.format(cmd))
                    break
                sleep(1)

        self._log.debug('RETURNCODE: {0}'.format(return_code))
        return return_code

    def _job_status(self):
        """
        :return: Return whether a binary is running
        :rtype: bool
        """
        return bool(self._find_application_processes())

    def _job_stop(self):
        """Stop any instances of a running binary"""
        procs = self._find_application_processes()
        for p in procs:
            p.terminate()
        gone, alive = psutil.wait_procs(procs, 10)
        for p in alive:
            p.kill()
        self._log.info('Stopped pid(s) {0}'.format([p.pid for p in procs]))
        return 0

    def _find_application_processes(self):
        """
        :rtype: list of psutil.Process
        """
        processes = list()
        for p in psutil.process_iter():
            try:
                if p.exe == self.command:
                    processes.append(p)
            except psutil.AccessDenied:
                continue
            except psutil.NoSuchProcess:
                continue

        return processes

    def _service_start(self):
        """
        :return: int return code of the start command
        :rtype: int
        """
        self._log.info('Starting {0}'.format(self.name))
        return self._service_interface('start')

    def _service_status(self):
        """
        :return: Whether the status command exited with 0
        :rtype: bool
        """
        return self._service_interface('status') == 0

    def _service_stop(self):
        self._log.info('Stopping {0}'.format(self.name))
        return self._service_interface('stop')

    def _service_interface(self, action):
        """
        Use the /sbin/service utility to get start/stop/status of a daemon.
        Return the process return code of the operation.
        :type action: str
        :return: The return code of the command.
        :rtype: int
        """
        return_code = -1
        cmd = '/sbin/service {0} {1}'.format(self.script_name, action)

        with open(os.devnull, 'w') as devnull:
            p = psutil.Popen(shlex.split(cmd), stdout=devnull, stderr=devnull)
            while True:
                return_code = p.poll()
                if return_code is not None:  # None = still running
                    break
                elif p.status == psutil.STATUS_ZOMBIE:
                    self._log.warning(
                        '{0} command resulted in a zombie process. '
                        'Returning with -1'.format(action))
                    break
                sleep(1)

        self._log.debug('RETURNCODE: {0}'.format(return_code))
        return return_code


class WindowsProcessClient(ProcessClient):
    def __init__(self, *args, **kwargs):
        ProcessClient.__init__(self, *args, **kwargs)

        from spot.zoom.agent.sentinel.client.wmi_client import WMIServiceClient
        self._wmi = WMIServiceClient(self.script_name)

    def _service_start(self):
        self._log.info('Starting service {0}'.format(self.script_name))
        return self._wmi.start()

    def _service_status(self):
        return self._wmi.status()

    def _service_stop(self):
        self._log.info('Stopping service {0}'.format(self.script_name))
        return self._wmi.stop()
