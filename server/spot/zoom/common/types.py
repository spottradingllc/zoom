

class AlertActionType():
    TRIGGER = 'trigger'
    RESOLVE = 'resolve'


class ApplicationType():
    JOB = "job"
    APPLICATION = "application"


class ApplicationState():
    OK = "ok"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
    NOTIFY = "notify"


class ApplicationStatus():
    RUNNING = 1
    STARTING = 2
    STOPPED = 3
    CRASHED = -99


class CommandType():
    CANCEL = "cancel"


class JobState():
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'


class OperationType():
    ADD = 'add'
    REMOVE = 'remove'


class PlatformType():
    UNKNOWN = -1
    LINUX = 0
    WINDOWS = 1


class PredicateType():
    AND = "and"
    OR = "or"
    NOT = "not"
    HEALTH = "health"
    HOLIDAY = "holiday"
    PROCESS = "process"
    TIME = "time"
    WEEKEND = "weekend"
    ZOOKEEPERNODEEXISTS = "zookeepernodeexists"
    ZOOKEEPERHASCHILDREN = "zookeeperhaschildren"
    ZOOKEEPERHASGRANDCHILDREN = "zookeeperhasgrandchildren"
    ZOOKEEPERGOODUNTILTIME = "zookeepergooduntiltime"


class UpdateType():
    APPLICATION_STATE_UPDATE = "application_state"
    APPLICATION_DEPENDENCY_UPDATE = "application_dependency"
    GLOBAL_MODE_UPDATE = "global_mode"
    TIMING_UPDATE = "timing_estimate"


class Weekdays():
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
