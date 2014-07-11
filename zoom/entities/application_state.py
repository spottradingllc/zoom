import datetime

from zoom.entities.types import ApplicationStatus


class ApplicationState(object):
    def __init__(self, application_name=None, configuration_path=None,
                 application_status=None, application_host=None,
                 start_time=None, error_state=None, local_mode=None):
        self._application_name = application_name
        self._configuration_path = configuration_path
        self._application_status = application_status
        self._application_host = application_host
        self._start_time = start_time
        self._error_state = error_state
        self._local_mode = local_mode

    def __del__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def __eq__(self, other):
        return self._configuration_path == other._configuration_path

    def __ne__(self, other):
        return self._configuration_path != other._configuration_path

    def __repr__(self):
        return (
            "{0}(application_name={0}, configuration_path={1}, "
            "application_status={2}, application_host={3}, start_time={4}, "
            "error_state={5}, local_mode={6}"
            .format(self.__class__.__name__,
                    self._application_name,
                    self._configuration_path,
                    self._application_status,
                    self._application_host,
                    self._start_time,
                    self._error_state,
                    self._local_mode)
        )

    @property
    def application_name(self):
        return self._application_name

    @property
    def configuration_path(self):
        return self._configuration_path

    @property
    def application_status(self):
        if self._application_status == ApplicationStatus.RUNNING:
            return "running"
        elif self._application_status == ApplicationStatus.STARTING:
            return "starting"
        elif self._application_status == ApplicationStatus.STOPPED:
            return "stopped"

        return "unknown"

    @property
    def application_host(self):
        if self._application_host is not None:
            return self._application_host

        return ""

    @property
    def start_time(self):
        if self._start_time is not None:
            return datetime.datetime.fromtimestamp(self._start_time).strftime('%Y-%m-%d %H:%M:%S')

        return ""

    def to_dictionary(self):
        result = {
            'application_name': self.application_name,
            'configuration_path': self.configuration_path,
            'application_status': self.application_status,
            'application_host': self.application_host,
            'start_time': self.start_time,
            'error_state': self._error_state,
        }

        return result