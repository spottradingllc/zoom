

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
