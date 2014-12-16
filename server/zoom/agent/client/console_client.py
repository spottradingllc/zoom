import logging
import re
from time import sleep
from subprocess import Popen, PIPE


class ConsoleServiceClient(object):
    def __init__(self, service_name):
        self._service_name = service_name
        self._log = logging.getLogger('rs.{0}'.format(__file__))

    def start(self):
        """
        Start service with console command.
        """
        command = r'SC START "{0}"'.format(self._service_name)
        retcode, stdout = self._run_cmd(command)
        return retcode

    def stop(self):
        """
        Stop service with console command.
        """
        command = r'SC STOP "{0}"'.format(self._service_name)
        counter = 0

        if not self.status():
            return 0

        retcode, stdout = self._run_cmd(command)

        # Check if service has stopped yet
        while self.status() and counter < 10:
            counter += 1
            sleep(1)

        # If still running after stop command
        pid = self.status(pid=True)
        if pid:
            self._log.info('Service did not respond to "stop" in a timely '
                           'manner. Killing the PID {0}.'.format(pid))
            retcode = self.kill(pid)

        return retcode

    def status(self, pid=False):
        """
        Run SC command to return the 'state' of the service.
        """
        process_id = 0
        command = r'SC queryex "{0}"'.format(self._service_name)

        retcode, stdout = self._run_cmd(command)

        match = re.search('PID\s+:\s(\d+)', stdout)
        if match:
            pid = int(match.group(1))

        self._log.debug('Process is running: {0}'.format(bool(process_id)))
        if pid:
            return process_id
        else:
            return bool(process_id)

    def kill(self, pid):
        """
        Kill process with console command.
        :type pid: int
        """
        command = r'TASKKILL /PID /F %d '.format(pid)
        retcode, stdout = self._run_cmd(command)
        return retcode

    def _run_cmd(self, cmd):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        if stderr:
            self._log.warning('From STDERR: {0}'.format(stderr))

        return p.returncode, stdout

    def __repr__(self):
        return '{0}(service="{1}")'.format(self.__class__.__name__,
                                           self._service_name)

    def __str__(self):
        return self.__repr__()