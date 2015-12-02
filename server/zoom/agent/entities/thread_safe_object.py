class ThreadSafeObject(object):
    def __init__(self, value, callback=None):
        self.value = value
        self._callback = callback

    def set_value(self, value, run_callback=True):
        self.value = value
        if self._callback is not None and run_callback:
            self._callback()

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

    def __init__(self, val, callback=None):
        ThreadSafeObject.__init__(self, val, callback=callback)
