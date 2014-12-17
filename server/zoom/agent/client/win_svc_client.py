import logging
import re
from subprocess import Popen, PIPE

from zoom.agent.entities.wsservice import WService


class WinSvcStates():
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    TIMEDOUT = 'TIMEDOUT'
    STARTING = 'STARTING'
    STOPPING = 'STOPPING'


class WindowsServiceClient(WService):
    def __init__(self, service_name):
        WService.__init__(self, service_name)
        self._log = logging.getLogger('sent.process')

    def start_wait(self, wait_for_status=None, timeout=None):
        retcode = 0
        self.start()
        if wait_for_status is not None:
            state = self.fetchstatus(wait_for_status, timeout=timeout)
            if state == WinSvcStates.TIMEDOUT:
                retcode = 1

        return retcode

    def stop_wait(self, wait_for_status=None, timeout=None, force=False):
        retcode = 0

        if self.status() == WinSvcStates.STOPPED:
            return retcode

        self.stop()
        if wait_for_status:
            state = self.fetchstatus(wait_for_status, timeout=timeout)
            if state == WinSvcStates.TIMEDOUT and force:
                retcode = self.kill(self.get_pid())

        return retcode

    def status_bool(self):
        return self.status() in [WinSvcStates.RUNNING, WinSvcStates.STARTING]

    def kill(self, pid):
        """
        Kill process with console command.
        :type pid: int
        """
        if pid == 0:
            return 0
        command = r'TASKKILL /PID /F %d '.format(pid)
        retcode, stdout = self._run_cmd(command)
        return retcode

    def get_pid(self):
        """
        Run SC command to return the 'state' of the service.
        """
        process_id = 0
        command = r'SC queryex "{0}"'.format(self.userv)

        retcode, stdout = self._run_cmd(command)

        match = re.search('PID\s+:\s(\d+)', stdout)
        if match:
            process_id = int(match.group(1))

        return process_id

    def _run_cmd(self, cmd):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()

        if stderr:
            self._log.warning('From STDERR: {0}'.format(stderr))

        return p.returncode, stdout
