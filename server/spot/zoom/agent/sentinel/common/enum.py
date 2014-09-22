

class ApplicationType():
    JOB = "job"
    APPLICATION = "application"


class PlatformType():
    UNKNOWN = -1
    LINUX = 0
    WINDOWS = 1


class JobState():
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'


class ApplicationState():
    OK = "ok"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
    NOTIFY = "notify"


class Weekdays():
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6