import datetime
import logging
import os
import psutil
import socket

from multiprocessing import Lock
from time import sleep, time

from zoom.common.types import (
    ApplicationType,
    ApplicationStatus
)
from zoom.agent.client.graphite_client import GraphiteClient


class ProcessClient(object):
    def __init__(self, name=None, start_cmd=None, stop_cmd=None,
                 status_cmd=None, script=None, apptype=None, restart_logic=None,
                 graphite_metric_names={}, cancel_flag=None):
        """
        :type name: str or None
        :type start_cmd: str or None
        :type stop_cmd: str or None
        :type status_cmd: str or None
        :type script: str or None
        :type apptype: zoom.common.types.ApplicationType
        :type restart_logic: zoom.agent.entities.restart.RestartLogic
        :type graphite_metric_names: dict
        :type cancel_flag: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        """
        assert any((name, start_cmd, script)), \
            ('Cannot initialize ProcessClient if name, command, and script'
             ' are all None.')

        self._log = logging.getLogger('sent.{0}.process'.format(name))
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.status_cmd = status_cmd
        self.name = name
        self.process_client_lock = Lock()  # lock for synchronous decorator
        self._script = script
        self._apptype = apptype
        self.restart_logic = restart_logic
        self.cancel_flag = cancel_flag

        self.last_status = False
        self._graphite_metric_names = graphite_metric_names

    @property
    def script_name(self):
        if self._script is not None:
            return self._script
        else:
            return self.name

    @property
    def start_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._process_start
        elif self._apptype == ApplicationType.APPLICATION:
            if self.start_cmd is not None:  # custom start command
                return self._process_start
            else:
                return self._service_start

    @property
    def status_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._process_status
        elif self._apptype == ApplicationType.APPLICATION:
            if self.status_cmd is not None:  # custom status command
                return self._process_status
            else:
                return self._service_status

    @property
    def stop_method(self):
        if self._apptype == ApplicationType.JOB:
            return self._process_stop
        elif self._apptype == ApplicationType.APPLICATION:
            if self.stop_cmd is not None:  # custom stop command
                return self._process_stop
            else:
                return self._service_stop

    @property
    def reset_counters(self):
        return self.restart_logic.reset_count

    def running(self):
        """
        :return: Whether the process is running.
        :rtype: bool
        """
        self.last_status = self.status_method()
        self.restart_logic.check_for_crash(self.last_status)
        self.send_to_graphite(self._graphite_metric_names.get('updown'),
                              (1 if self.last_status else 0))
        self._log.debug('Process {0} running: {1}, crashed={2}'
                        .format(self.name, self.last_status,
                                self.restart_logic.crashed))
        return self.last_status

    def start(self):
        """Try to start process"""
        if self.restart_logic.stay_down:
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
            self.send_to_graphite(self._graphite_metric_names.get('result'),
                                  return_code)
            self.send_to_graphite(self._graphite_metric_names.get('runtime'),
                                  finish_time - start_time)

            if return_code == 0:
                self._log.info('{0} start successful in {1} tries.'
                               .format(self.name, self.restart_logic.count))
                self.reset_counters()
                break
            elif return_code == ApplicationStatus.CANCELLED:
                self._log.info('Start has been cancelled.')
                break
            else:
                self._log.info('{0} start attempt {1} failed.'
                               .format(self.name, self.restart_logic.count))
                self._stop_if_running()
                self._log.debug('Waiting 10 seconds before trying again.')
                sleep(10)  # minor wait before we try again

        self.restart_logic.set_ran_stop(False)

        return return_code

    def stop(self, **kwargs):
        """Stop process"""
        self.restart_logic.set_ran_stop(True)

        if kwargs.get('stay_down', 'false') == 'true':
            self.restart_logic.set_stay_down(True)
        else:
            self.restart_logic.set_stay_down(False)

        return_code = self.stop_method()

        if return_code != 0:
            self._log.error('There was some issue with the stop command. '
                            'Return code was: {0}'.format(return_code))

        if self.running():
            self._log.error('App is still running after running stop!')

        return return_code

    def send_to_graphite(self, metric, data, tstamp=None, env=None):
        if not metric:
            return
        try:
            GraphiteClient.send(metric, data, tstamp=tstamp, env=env)
        except socket.timeout:
            self._log.error('Could not connect to Graphite')
        except IOError as e:
            self._log.error('Graphite/HAProxy not available: {0}'.format(e))
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
            
    def _process_start(self):
        """
        Start process by running some arbitrary command
        """
        self._log.info('Running command: {0}'.format(self.start_cmd))
        return self._run_command(self.start_cmd)

    def _process_status(self):
        """
        :return: Return whether a binary is running
        :rtype: bool
        """
        if self.status_cmd is not None:
            # -2 is a cancelled process run.
            # Ignore these b/c otherwise we think it's a crash
            return self._run_command(self.status_cmd, stdout=False) in (0, -2)
        else:
            return bool(self._find_application_processes())

    def _process_stop(self):
        """Stop any instances of a running binary"""
        if self.stop_cmd is not None:
            return self._run_command(self.stop_cmd)
        else:
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
                if p.exe == self.start_cmd:
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
        # -2 is a cancelled process run.
        # Ignore these b/c otherwise we think it's a crash
        return self._service_interface('status') in (0, -2)

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
        stdout = (False if action == 'status' else True)
        return self._run_command(cmd, stdout=stdout)

    def _run_command(self, cmd, stdout=True):
        """
        Generic command runner
        :type cmd: str
        :rtype: int
        """
        outfile = self._get_cmd_outfile(stdout)
        return_code = -1
        with open(outfile, 'a') as outfile:
            # log out a timestamp so we know when the command was run
            outfile.write('{0}: "{1}"\n'.format(datetime.datetime.now(), cmd))

            p = psutil.Popen(cmd, stdout=outfile, stderr=outfile, shell=True)
            while True:
                return_code = p.poll()
                if return_code is not None:  # None = still running
                    break
                elif p.status == psutil.STATUS_ZOMBIE:
                    self._log.warning(
                        '{0} command resulted in a zombie process. '
                        'Returning with 0'.format(cmd))
                    return_code = 0
                    break
                elif self.cancel_flag == True:
                    p.terminate()
                    return_code = -2
                    self._log.info('Command {0} was cancelled.'.format(cmd))
                    self.cancel_flag.set_value(False)
                    break
                sleep(1)

        self._log.debug('RETURNCODE: {0}'.format(return_code))
        return return_code

    def _get_cmd_outfile(self, stdout):
        """
        For every init script log out stdout/err to a file on 'start' or 'stop'.
        :type stdout: bool
        :rtype: str
        """
        if not stdout:
            # _file = os.devnull
            dt = datetime.date.today().strftime('%Y%m%d')
            _file = 'logs/{0}_status_output.{1}.log'.format(self.script_name, dt)
        else:
            dt = datetime.date.today().strftime('%Y%m%d')
            _file = 'logs/{0}_script_output.{1}.log'.format(self.script_name, dt)

        return _file


class WindowsProcessClient(ProcessClient):
    def __init__(self, *args, **kwargs):
        ProcessClient.__init__(self, *args, **kwargs)

        from zoom.agent.entities.wsservice import WinSvcStates, WService
        self._states = WinSvcStates
        self._wsc = WService(self.script_name)

    def _service_start(self):
        self._log.info('Starting service {0}'.format(self.script_name))
        return self._wsc.start_wait()

    def _service_status(self):
        return self._wsc.status_bool()

    def _service_stop(self):
        self._log.info('Stopping service {0}'.format(self.script_name))
        return self._wsc.stop_wait(wait_for_status=self._states.STOPPED,
                                   timeout=10,
                                   force=True)
