"""
Module for manipulating WinNT, Win2k & WinXP services.
Requires the win32all package which can be retrieved
from => http://starship.python.net/crew/mhammond

Based largely on:
http://code.activestate.com/recipes/115875-controlling-windows-services/
"""
import logging
import re
import time
from subprocess import Popen, PIPE
import win32api as wa
import win32con as wc
import win32service as ws


class WinSvcStates():
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    TIMEDOUT = 'TIMEDOUT'
    STARTING = 'STARTING'
    STOPPING = 'STOPPING'
    NOSERVICE = 'NOSERVICE'


EXPECTED_STATUS_MAP = {
    WinSvcStates.RUNNING: ws.SERVICE_RUNNING,
    WinSvcStates.STOPPED: ws.SERVICE_STOPPED,
    WinSvcStates.STARTING: ws.SERVICE_START_PENDING,
    WinSvcStates.STOPPING: ws.SERVICE_STOP_PENDING,
}

class WService(object):
    """
    The WService Class is used for controlling WinNT, Win2k & WinXP like
    services. Just pass the name of the service you wish to control to the
    class instance and go from there. For example, if you want to control
    the Workstation service try this:

        import WService
        workstation = WService.WService("Workstation")
        workstation.start()
        workstation.fetchstatus("running", 10)
        workstation.stop()
        workstation.fetchstatus("stopped")

    Creating an instance of the WService class is done by passing the name of
    the service as it appears in the Management Console or the short name as
    it appears in the registry. Mixed case is ok.
        cvs = WService.WService("CVS NT Service 1.11.1.2 (Build 41)")
            or
        cvs = WService.WService("cvs")

    If needing remote service control try this:
        cvs = WService.WService("cvs", r"\\CVS_SERVER")
            or
        cvs = WService.WService("cvs", "\\\\CVS_SERVER")

    The WService Class supports these methods:

        start:          Starts service.
        stop:           Stops service.
        restart:        Stops and restarts service.
        pause:          Pauses service (Only if service supports feature).
        resume:         Resumes service that has been paused.
        status:         Queries current status of service.
        fetchstatus:    Continually queries service until requested status(STARTING, RUNNING,
                            STOPPING & STOPPED) is met or timeout value(in seconds) reached.
                            Default timeout value is infinite.
        infotype:       Queries service for process type. (Single, shared and/or
                            interactive process)
        infoctrl:       Queries control information about a running service.
                            i.e. Can it be paused, stopped, etc?
        infostartup:    Queries service Startup type. (Boot, System,
                            Automatic, Manual, Disabled)
        setstartup      Changes/sets Startup type. (Boot, System,
                            Automatic, Manual, Disabled)
        getname:        Gets the long and short service names used by Windows.
                            (Generally used for internal purposes)
    """

    def __init__(self, service, machinename=None, dbname=None):
        self._log = logging.getLogger('WService.{0}'.format(service.replace(' ', '')))
        self.userv = service
        self.machinename = machinename
        self.dbname = dbname
        self._scmhandle = None
        self.sserv = None
        self.lserv = None
        self.sccss = "SYSTEM\\CurrentControlSet\\Services\\"

        if self.handle is None:
            self._log.error('The service %s does not exist!' % service)

    @property
    def scmhandle(self):
        """
        Connection to the service manager. Refresh the connection on every
        request if the service name is None (service doesn't exist). The service
        may have been created after startup.
        """
        if self._scmhandle is None or None in (self.sserv, self.lserv):
            self._scmhandle = ws.OpenSCManager(self.machinename, self.dbname,
                                               ws.SC_MANAGER_ALL_ACCESS)

        return self._scmhandle

    @property
    def handle(self):
        """
        If the service names are None, try to get them again. If they are STILL
        None, the service doesn't exist yet, and return a None handle.
        """
        if None in (self.sserv, self.lserv):
            self.sserv, self.lserv = self.getname()

        if None in (self.sserv, self.lserv):
            return None
        else:
            return ws.OpenService(self.scmhandle, self.sserv, ws.SERVICE_ALL_ACCESS)

    def start(self):
        return ws.StartService(self.handle, None)

    def start_wait(self, wait_for_status=None, timeout=None):
        if self.handle is None:
            self._log.error('Cannot start. Service %s does not exist!' % self.userv)
            return -1

        retcode = 0
        self.start()
        if wait_for_status is not None:
            state = self.fetchstatus(wait_for_status, timeout=timeout)
            if state == WinSvcStates.TIMEDOUT:
                retcode = 1

        return retcode

    def stop(self):
        return ws.ControlService(self.handle, ws.SERVICE_CONTROL_STOP)

    def stop_wait(self, wait_for_status=None, timeout=None, force=False):
        if self.handle is None:
            self._log.error('Cannot stop. Service %s does not exist!' % self.userv)
            return -1

        retcode = 0

        if self.status() == WinSvcStates.STOPPED:
            return retcode

        self.stop()
        if wait_for_status is not None:
            state = self.fetchstatus(wait_for_status, timeout=timeout)
            if state == WinSvcStates.TIMEDOUT and force:
                retcode = self.kill(self.get_pid())

        return retcode

    def restart(self):
        self.stop()
        self.fetchstatus(WinSvcStates.STOPPED)
        self.start()

    def pause(self):
        return ws.ControlService(self.handle, ws.SERVICE_CONTROL_PAUSE)

    def resume(self):
        return ws.ControlService(self.handle, ws.SERVICE_CONTROL_CONTINUE)

    def status(self, prn=0):
        stat = self._query_status()
        if stat is None:
            self._log.debug('The %s service does not exist.' % self.userv)
            return WinSvcStates.NOSERVICE
        if stat[1] == ws.SERVICE_STOPPED:
            if prn == 1:
                self._log.info("The %s service is stopped." % self.lserv)
            else:
                return WinSvcStates.STOPPED
        elif stat[1] == ws.SERVICE_START_PENDING:
            if prn == 1:
                self._log.info("The %s service is starting." % self.lserv)
            else:
                return WinSvcStates.STARTING
        elif stat[1] == ws.SERVICE_STOP_PENDING:
            if prn == 1:
                self._log.info("The %s service is stopping." % self.lserv)
            else:
                return WinSvcStates.STOPPING
        elif stat[1] == ws.SERVICE_RUNNING:
            if prn == 1:
                self._log.debug("The %s service is running." % self.lserv)
            else:
                return WinSvcStates.RUNNING

    def status_bool(self):
        return self.status() in [WinSvcStates.RUNNING, WinSvcStates.STARTING]

    def fetchstatus(self, fstatus, timeout=None):
        _status = fstatus.upper()
        if timeout is not None:
            timeout = int(timeout)
            timeout *= 2

        def to(timeout):
            time.sleep(.5)
            if timeout is not None:
                if timeout > 1:
                    timeout -= 1
                    return timeout
                else:
                    return "TO"

        while 1:
            stat = self._query_status()
            if stat is None:
                return WinSvcStates.NOSERVICE
            elif stat[1] == EXPECTED_STATUS_MAP.get(_status):
                return _status
            else:
                timeout = to(timeout)
                if timeout == "TO":
                    return WinSvcStates.TIMEDOUT

    def infotype(self):
        stat = self._query_status()
        if stat is None:
            self._log.info('The %s service does not exist.' % self.userv)
        if stat[0] and ws.SERVICE_WIN32_OWN_PROCESS:
            self._log.info("The %s service runs in its own process." % self.lserv)
        if stat[0] and ws.SERVICE_WIN32_SHARE_PROCESS:
            self._log.info("The %s service shares a process with other services." % self.lserv)
        if stat[0] and ws.SERVICE_INTERACTIVE_PROCESS:
            self._log.info("The %s service can interact with the desktop." % self.lserv)

    def infoctrl(self):
        stat = self._query_status()
        if stat is None:
            self._log.info('The %s service does not exist.' % self.userv)
        if stat[2] and ws.SERVICE_ACCEPT_PAUSE_CONTINUE:
            self._log.info("The %s service can be paused." % self.lserv)
        if stat[2] and ws.SERVICE_ACCEPT_STOP:
            self._log.info("The %s service can be stopped." % self.lserv)
        if stat[2] and ws.SERVICE_ACCEPT_SHUTDOWN:
            self._log.info("The %s service can be shutdown." % self.lserv)

    def infostartup(self):
        isuphandle = wa.RegOpenKeyEx(wc.HKEY_LOCAL_MACHINE,
                                     self.sccss + self.sserv, 0, wc.KEY_READ)
        isuptype = wa.RegQueryValueEx(isuphandle, "Start")[0]
        wa.RegCloseKey(isuphandle)

        return {
            0: "boot",
            1: "system",
            2: "automatic",
            3: "manual",
            4: "disabled",
        }.get(isuptype, 'Unknown')

    def setstartup(self, startuptype):
        sut = startuptype.lower()

        if sut == "boot":
            suptype_id = 0
        elif sut == "system":
            suptype_id = 1
        elif sut == "automatic":
            suptype_id = 2
        elif sut == "manual":
            suptype_id = 3
        elif sut == "disabled":
            suptype_id = 4

        if self.handle is None:
            self._log.info('The %s service does not exist.' % self.userv)
        else:
            ws.ChangeServiceConfig(self.handle, ws.SERVICE_NO_CHANGE,
                                   suptype_id, ws.SERVICE_NO_CHANGE, None, None,
                                   0, None, None, None, self.lserv)

    def getname(self):
        for i in ws.EnumServicesStatus(self.scmhandle):
            if i[0].lower() == self.userv.lower():
                return i[0], i[1]
            if i[1].lower() == self.userv.lower():
                return i[0], i[1]

        return None, None

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

    def _query_status(self):
        if self.handle is None:
            return None
        else:
            return ws.QueryServiceStatus(self.handle)