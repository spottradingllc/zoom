from datetime import datetime

from zoom.common.types import ApplicationStatus


class ApplicationState(object):
    def __init__(self, application_name=None, configuration_path=None,
                 application_status=None, application_host=None,
                 completion_time=None, trigger_time=None, error_state=None,
                 local_mode=None, delete=False, login_user=None,
                 last_command=None, fqdn=None, grayed=None, pd_disabled=None):
        self._application_name = application_name
        self._configuration_path = configuration_path
        self._application_status = application_status
        self._application_host = application_host
        self._completion_time = completion_time
        self._trigger_time = trigger_time
        self._error_state = error_state
        self._local_mode = local_mode
        self._delete = delete
        self._login_user = login_user
        self._fqdn = fqdn
        self._last_command = last_command
        self._grayed = grayed
        self._pd_disabled = pd_disabled

    def __del__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        pass

    def __eq__(self, other):
        return self._configuration_path == other.configuration_path

    def __ne__(self, other):
        return self._configuration_path != other.configuration_path

    def __repr__(self):
        return str(self.to_dictionary())

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
    def completion_time(self):
        if self._completion_time is not None and \
                self._error_state not in ('starting', 'stopping'):
            return datetime.fromtimestamp(
                self._completion_time).strftime('%Y-%m-%d %H:%M:%S')

        return ""

    def to_dictionary(self):
        return {
            'application_name': self.application_name,
            'configuration_path': self.configuration_path,
            'application_status': self.application_status,
            'application_host': self.application_host,
            'completion_time': self.completion_time,
            'trigger_time': self._trigger_time,
            'error_state': self._error_state,
            'delete': self._delete,
            'local_mode': self._local_mode,
            'login_user': self._login_user,
            'fqdn': self._fqdn,
            'last_command': self._last_command,
            'grayed': self._grayed,
            'pd_disabled': self._pd_disabled
        }
