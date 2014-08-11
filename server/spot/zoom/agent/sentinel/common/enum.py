

class SimpleObject(object):
    def __init__(self, value):
        self.value = value

    def set_value(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '{0}(value={1})'.format(self.__class__.__name__, self.value)


class ApplicationMode(SimpleObject):
    AUTO = "auto"
    MANUAL = "manual"

    def __init__(self, val):
        SimpleObject.__init__(self, val)


class ApplicationType():
    JOB = "job"
    APPLICATION = "application"


class PlatformType():
    UNKNOWN = -1
    LINUX = 0
    WINDOWS = 1


class PredicateType():
    AND = "and"
    OR = "or"
    NOT = "not"
    HEALTH = "health"
    PROCESS = "process"
    ZOOKEEPERNODEEXISTS = "zookeepernodeexists"
    ZOOKEEPERHASCHILDREN = "zookeeperhaschildren"
    ZOOKEEPERHASGRANDCHILDREN = "zookeeperhasgrandchildren"
    ZOOKEEPERGOODUNTILTIME = "zookeepergooduntiltime"


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