import logging
from spot.zoom.agent.sentinel.config.constants import CALLBACK_PRIORITY


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
        self._started = False

    @property
    def met(self):
        return self._met

    def add_callback(self, cb):
        """
        :type cb: dict ({str: types.funcType})
        """
        self._callbacks.append(cb)
        self._sort_callbacks()

    def _sort_callbacks(self):
        """
        Sort callbacks based on CALLBACKS dictionary values
        """
        self._callbacks = sorted(self._callbacks,
                                 key=lambda item: [CALLBACK_PRIORITY.get(k, 99)
                                                   for k in item.keys()])

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

        for item in self._callbacks:
            for cb in item.values():
                self._log.debug('{0}: About to run callback.'.format(self))
                cb()

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.debug('Stopping {0}'.format(self))
            self._started = False
        else:
            self._log.debug('Already stopped {0}'.format(self))

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
        return all([
            self._met == other._met,
            self._parent == other._parent,
            self._comp_name == other._comp_name])

    def __ne__(self, other):
        return any([
            self._met != other._met,
            self._parent != other._parent,
            self._comp_name != other._comp_name])