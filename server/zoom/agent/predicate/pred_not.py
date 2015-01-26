import logging
from zoom.agent.predicate.simple import SimplePredicate


class PredicateNot(SimplePredicate):
    def __init__(self, comp_name, settings, pred, parent=None):
        """
        :type comp_name: str
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type pred: zoom.agent.entities.dependency object
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.dependency = pred
        self._log = logging.getLogger('sent.{0}.pred.not'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    @property
    def met(self):
        return not self.dependency.met

    @property
    def operationally_relevant(self):
        return self.dependency.operationally_relevant and self.dependency.met

    @property
    def started(self):
        return all([self._started, self.dependency.started])

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self.dependency.start()
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.debug('Stoping {0}'.format(self))
            self._started = False
            self.dependency.stop()
        else:
            self._log.debug('Already stopped {0}'.format(self))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, started={3}, met={4}, '
                'predicate={5})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.started,
                        self.met,
                        self.dependency))

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.dependency == getattr(other, 'dependency', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.dependency != getattr(other, 'dependency', None)
        ])
