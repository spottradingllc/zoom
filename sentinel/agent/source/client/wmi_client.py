import logging
import pythoncom

from subprocess import Popen, PIPE
from time import sleep
from wmi import WMI, x_wmi


class WMIServiceClient(object):
    def __init__(self, service_name):
        self._service_name = service_name
        self._log = logging.getLogger('sent.process')

    @property
    def functional(self):
        """
        This function checks whether a WMI call will be successful.
        :rtype: bool
        """
        try:
            c = WMI()
            service = c.Win32_Service(Name=self._service_name)
            if not service:
                self._log.warning('WMI success, but could not find service')
                raise Exception('Script was unable to find service on the '
                                'server. Check service name for validity.')
            else:
                self._log.debug('WMI success, & found service')
                return True
        except x_wmi:
            self._log.warning('COM Error: The RPC server is unavailable. '
                              'WMI call has failed.')
            return False

    def start(self):
        """
        Start service with WMI
        :rtype: int
        """
        pythoncom.CoInitialize()
        c = WMI()
        for service in c.Win32_Service(Name=self._service_name):
            retval = service.StartService()
            return retval[0]

    def stop(self):
        """
        Start service with WMI
        :rtype: int
        """
        returncode = -1
        counter = 0

        pythoncom.CoInitialize()
        c = WMI()

        # Run stop with WMI
        for service in c.Win32_Service(Name=self._service_name):
            retval = service.StopService()
            returncode = retval[0]

        # Check if service has stopped yet
        while self.status() and counter < 10:
            counter += 1
            sleep(1)

        # If still running after stop command
        pid = self.status(pid=True)
        if pid:
            self._log.info('Service did not respond to "stop" in a timely '
                           'manner. Killing the PID {0}.'.format(pid))
            for process in c.Win32_Process(ProcessId=pid):
                retval = process.Terminate()
                returncode = retval[0]

        # If still running after attempt at process termination via WMI
        if self.status():
            self._log.warning('Service could not be killed with WMI. '
                              'Trying console command: TASKKILL')
            cmd = "TASKKILL /F /PID {0}".format(pid)
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            p.wait()
            returncode = p.returncode

        return returncode

    def status(self, pid=False):
        """
        Make WMI call to server to get whether the service is running.
        :rtype: int or bool
        """
        process_id = 0
        pythoncom.CoInitialize()
        c = WMI()
        for service in c.Win32_Service(Name=self._service_name):
            process_id = service.ProcessId
        self._log.debug('Process is running: {0}'.format(bool(process_id)))
        if pid:
            return process_id
        else:
            return bool(process_id)

    def __repr__(self):
        return '{0}(service="{1}")'.format(self.__class__.__name__,
                                           self._service_name)

    def __str__(self):
        return self.__repr__()
