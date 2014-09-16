class PredicateType():
    AND = "and"
    OR = "or"
    NOT = "not"
    HEALTH = "health"
    HOLIDAY = "holiday"
    PROCESS = "process"
    WEEKEND = "weekend"
    ZOOKEEPERNODEEXISTS = "zookeepernodeexists"
    ZOOKEEPERHASCHILDREN = "zookeeperhaschildren"
    ZOOKEEPERHASGRANDCHILDREN = "zookeeperhasgrandchildren"
    ZOOKEEPERGOODUNTILTIME = "zookeepergooduntiltime"

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




