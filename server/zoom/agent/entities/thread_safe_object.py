class ThreadSafeObject(object):
    def __init__(self, value):
        self.value = value

    def set_value(self, value):
        self.value = value

    def get(self, key, default=None):
        if isinstance(self.value, dict):
            return self.value.get(key, default)
        else:
            return None

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return self.value != other

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '{0}(value={1})'.format(self.__class__.__name__, self.value)


class ApplicationMode(ThreadSafeObject):
    AUTO = "auto"
    MANUAL = "manual"

    def __init__(self, val):
        ThreadSafeObject.__init__(self, val)