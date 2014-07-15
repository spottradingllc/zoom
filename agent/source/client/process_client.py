import logging
import os
import shlex
import psutil
import socket

from multiprocessing import Lock
from time import sleep, time
from subprocess import PIPE
from source.common.enum import PlatformType, ApplicationType
from source.util.decorators import synchronous
from source.client.graphite_client import GraphiteClient
from source.config.constants import ( 
    GRAPHITE_RUNTIME_METRIC, 
    GRAPHITE_RESULT_METRIC
)


class ProcessClient(object):
    def __init__(self, name=None, command=None, script=None, apptype=None,
                 system=None, restart_max=None, graphite_app_metric=None):
        """
        :type name: str or None
        :type command: str or None
        :type script: str or None
        :type apptype: source.common.enum.ApplicationType
        :type system: source.common.enum.PlatformType
        :type restart_max: int or None
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
        self._startcount = 0
        self.restart_max = restart_max
        self.last_status = False
        self._graphite_app_metric = graphite_app_metric

    @property
    def script_name(self):
        if self._script is not None:
            return self._script
        else:
            return self.name

    @property
    def restart_max_reached(self):
        result = self._startcount >= self.restart_max
        if result:
            self._log.error('The restart max {0} has been reached. The '
                            'process will no longer try to start.'
                            .format(self.restart_max))
        return result
    
    def reset_counters(self):
        self._log.debug('Resetting start count to 0.')
        self._startcount = 0

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
        while not self.restart_max_reached:
            self._startcount += 1
            start_time = time()
            returncode = dostart()
            finish_time = time()
            if returncode == 0:
                self._log.info('{0} start successful in {1} tries.'
                               .format(self.name, self._startcount))
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
                    
        return returncode

    def stop(self):
        """Stop process"""
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
            GraphiteClient.send(metric, data, tstamp=None, env=None)
        except socket.timeout:
            self._log.error('Could not connect to Graphite')
        except IOError as e:
            self._log.error('Check shortage of file descriptor: {0}'.format(e))
        except Exception as e:
            self._log.error('Unknown exception while sending data to Graphite: {0}'
                            .format(e))

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

        p = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, errs = p.communicate()  # block until process is done
        self._log.debug('RETCODE: {0}'.format(p.returncode))
        self._log.debug('STDOUT: {0}'.format(out))
        self._log.debug('STDERR: {0}'.format(errs))
        return p.returncode

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
        return self._service_interface('start', block=True)

    def _service_status(self):
        """
        :return: Whether the status command exited with 0
        :rtype: bool
        """
        return self._service_interface('status', block=False) == 0

    def _service_stop(self):
        self._log.info('Stopping {0}'.format(self.name))
        return self._service_interface('stop', block=True)

    def _service_interface(self, action, block=False):
        """
        Use the /sbin/service utility to get start/stop/status of a daemon.
        Return the process return code of the operation.
        :type action: str
        :return: The return code of the command.
        :rtype: int
        """
        if block:
            exec_fn = None
        else:
            exec_fn = os.setsid

        cmd = '/sbin/service {0} {1}'.format(self.script_name, action)
        p = psutil.Popen(shlex.split(cmd),
                         stdout=PIPE, stderr=PIPE,
                         preexec_fn=exec_fn
                         )

        out, err = p.communicate()
        self._log.debug('RETURNCODE: {0}'.format(p.returncode))
        if out:
            self._log.debug('STDOUT: {0}'.format(out.rstrip('\n')))
        if err:
            self._log.warning('STDERR: {0}'.format(err.rstrip('\n')))
        return p.returncode
    
    def _append_metrics(self, base_metric):
        return base_metric.format(self._graphite_app_metric)      


class WindowsProcessClient(ProcessClient):
    def __init__(self, *args, **kwargs):
        ProcessClient.__init__(self, *args, **kwargs)

        from source.client.wmi_client import WMIServiceClient
        self._wmi = WMIServiceClient(self.script_name)

    def _service_start(self):
        self._log.info('Starting service {0}'.format(self.script_name))
        return self._wmi.start()

    def _service_status(self):
        return self._wmi.status()

    def _service_stop(self):
        self._log.info('Stopping service {0}'.format(self.script_name))
        return self._wmi.stop()
