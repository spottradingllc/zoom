import logging
import os
import shlex
import psutil
import socket

from multiprocessing import Lock
from time import sleep, time
from subprocess import call
from sentinel.common.enum import PlatformType, ApplicationType
from sentinel.common.restart import RestartLogic
from sentinel.util.decorators import synchronous
from sentinel.client.graphite_client import GraphiteClient
from sentinel.config.constants import ( 
    GRAPHITE_RUNTIME_METRIC, 
    GRAPHITE_RESULT_METRIC
)


class ProcessClient(object):
    def __init__(self, name=None, command=None, script=None, apptype=None,
                 system=None, restart_max=None, restart_on_crash=None,
                 graphite_app_metric=None):
        """
        :type name: str or None
        :type command: str or None
        :type script: str or None
        :type apptype: sentinel.common.enum.ApplicationType
        :type system: sentinel.common.enum.PlatformType
        :type restart_max: int or None
        :type restart_on_crash: bool or None
        """
        assert any((name, command, script)), ('Cannot initialize ProcessClient '
                                              'if name, command, and script are'
                                              ' all None.')

        self._log = logging.getLogger('sent.{0}.process'.format(name))
        self.command = command
        self.name = name
        self.process_client_lock = Lock()  # lock for synchronous decorator
        self._script = script
        self._apptype = apptype
        self._system = system
        self._restart_logic = RestartLogic(restart_on_crash, restart_max)

        self.last_status = False
        self._graphite_app_metric = graphite_app_metric

    @property
    def script_name(self):
        if self._script is not None:
            return self._script
        else:
            return self.name

    @property
    def reset_counters(self):
        return self._restart_logic.reset_count

    def running(self, reset=True):
        """
        :param reset: Whether to reset the start counters.
        :type reset: bool
        :return: Whether the process is running.
        :rtype: bool
        """
        if self._apptype == ApplicationType.JOB:
            self.last_status = self._job_status()
        elif self._apptype == ApplicationType.APPLICATION:
            self.last_status = self._service_status()

        self._log.debug('Process {0} running: {1}'
                        .format(self.name, self.last_status))
        if self.last_status and reset:
            self.reset_counters()
        return self.last_status

    @synchronous('process_client_lock')  # shares lock with PredicateProcess
    def start(self):
        """Try to start process"""
        if self._restart_logic.restart is False:
            self._log.info('Process crashed and restart_on_crash is False.')
            return 1
        else:
            self._log.debug('Restarts allowed.')

        if self._apptype == ApplicationType.JOB:
            dostart = self._job_start
        elif self._apptype == ApplicationType.APPLICATION:
            self._stop_if_running()

            if self.command is not None:
                dostart = self._job_start
            else:
                dostart = self._service_start

        returncode = -1
        metric_result = self._append_metrics(GRAPHITE_RESULT_METRIC)
        metric_runtime = self._append_metrics(GRAPHITE_RUNTIME_METRIC)        
        while not self._restart_logic.restart_max_reached:
            self._restart_logic.increment_count()
            start_time = time()
            returncode = dostart()
            finish_time = time()
            if returncode == 0:
                self._log.info('{0} start successful in {1} tries.'
                               .format(self.name, self._restart_logic.count))
                self.reset_counters()
                self.send_to_graphite(metric_result, returncode)
                self.send_to_graphite(metric_runtime, finish_time - start_time)
                break
            else:
                self._log.info('{0} start failed.'.format(self.name))
                self._stop_if_running()
                self._log.debug('Waiting 10 seconds before trying again.')
                self.send_to_graphite(metric_result, returncode)
                self.send_to_graphite(metric_runtime, finish_time - start_time)  
                sleep(10)  # minor wait before we try again

        self._restart_logic.set_false()
        return returncode

    def stop(self, arg_dict):
        """Stop process"""
        if arg_dict.get('argument', None) == '':    # if argument is empty, start is allowed
            self._restart_logic.set_true()
        returncode = -1
        if self._apptype == ApplicationType.JOB:
            returncode = self._job_stop()
        elif self._apptype == ApplicationType.APPLICATION:
            returncode = self._service_stop()

        if returncode != 0 or self.running(reset=False):
            self._log.error('There was some issue with the stop command.')

        return returncode

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
        # Stop if already running
        if self.running(reset=False):
            self._log.warning('The application is running. Attempting stop.')
            self.stop()
            
    def _job_start(self):
        """Start process by executing a binary."""
        self._log.info('Starting {0}'.format(self.command))
        if self._system == PlatformType.LINUX:
            cmd = shlex.split(self.command)
        else:
            cmd = self.command

        with open(os.devnull, 'w') as devnull:
            retcode = call(shlex.split(cmd), stdout=devnull, stderr=devnull)

        self._log.debug('RETURNCODE: {0}'.format(retcode))
        return retcode

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
        cmd = '/sbin/service {0} {1}'.format(self.script_name, action)

        with open(os.devnull, 'w') as devnull:
            retcode = call(shlex.split(cmd), stdout=devnull, stderr=devnull)

        self._log.debug('RETURNCODE: {0}'.format(retcode))
        return retcode
        # p.communicate was removed b/c there was issue that would never allow
        # the stdout or stderr .read() to return. It would block forever and the
        # process would become a zombie
        #
        # out, err = p.communicate()
        #
        # self._log.debug('RETURNCODE: {0}'.format(p.returncode))
        # if out:
        #     self._log.debug('STDOUT: {0}'.format(out.rstrip('\n')))
        # if err:
        #     self._log.warning('STDERR: {0}'.format(err.rstrip('\n')))
        # return p.returncode
    
    def _append_metrics(self, base_metric):
        return base_metric.format(self._graphite_app_metric)      


class WindowsProcessClient(ProcessClient):
    def __init__(self, *args, **kwargs):
        ProcessClient.__init__(self, *args, **kwargs)

        from sentinel.client.wmi_client import WMIServiceClient
        self._wmi = WMIServiceClient(self.script_name)

    def _service_start(self):
        self._log.info('Starting service {0}'.format(self.script_name))
        return self._wmi.start()

    def _service_status(self):
        return self._wmi.status()

    def _service_stop(self):
        self._log.info('Stopping service {0}'.format(self.script_name))
        return self._wmi.stop()
