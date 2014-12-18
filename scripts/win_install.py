import os
import psutil
import time
import win32event
import win32evtlogutil
import win32service
import win32serviceutil


class PythonService(win32serviceutil.ServiceFramework):
    _svc_name_ = "sentinel"
    _svc_display_name_ = "sentinel"
    _svc_deps_ = ["EventLog"]
    _proc = None

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        if self._proc:
            self._proc.terminate()

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        import servicemanager
        # Write a 'started' event to the event log...
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STARTED,
                                    0,  # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))
        self.main()

        # and write a 'stopped' event to the event log.
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STOPPED,
                                    0,  # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))

    def main(self):
        os.chdir(r"C:\Program Files\Spot Trading LLC\zoom\server")
        self._proc = psutil.Popen(r"C:\Python27\python.exe sentinel.py")
        try:
            while self._proc.status == psutil.STATUS_RUNNING:
                time.sleep(1)
        except psutil.NoSuchProcess:
            pass


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(PythonService)
