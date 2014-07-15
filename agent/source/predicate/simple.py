import logging


class SimplePredicate(object):
    def __init__(self, comp_name, parent=None):
        """
        :type comp_name: str
        :type parent: str or None
        """
        self._met = False
        self._parent = parent
        self._comp_name = comp_name
        self._callbacks = list()
        self._started = False
        self._log = logging.getLogger('sent.{0}.pred'.format(comp_name))

    @property
    def met(self):
        return self._met

    def add_callback(self, cb):
        """
        :type cb: types.funcType
        """
        self._callbacks.append(cb)

    def set_met(self, value):
        """
        Helper function to set the dependency 'met' value.
        :type value: bool
        """
        if self._met == value:
            self._log.debug('"Met" value is still {0}. Skipping.'.format(value))
            return

        self._log.info('Setting "met" attribute from {0} to {1} for {2} '
                       .format(self._met, value, self))
        self._met = value
        for cb in self._callbacks:
            self._log.debug('{0}: About to run callback.'.format(self))
            cb()

    def start(self):
        if not self._started:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        pass

    def reset(self):
        self._log.info('Resetting predicate for {0}'.format(self))
        self._started = False

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, met={3})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.met)
                )

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return type(self) == type(other)

    def __ne__(self, other):
        return type(self) != type(other)