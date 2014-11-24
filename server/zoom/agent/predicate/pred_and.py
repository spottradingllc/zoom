import logging
from zoom.agent.predicate.simple import SimplePredicate


class PredicateAnd(SimplePredicate):
    def __init__(self, comp_name, settings, predicates, parent=None):
        """
        :type comp_name: str
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type predicates: list of zoom.agent.entities.predicate objects
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.dependencies = predicates
        self._log = logging.getLogger('sent.{0}.pred.and'.format(comp_name))
        self._log.info('Registered {0}'.format(self))
        self._started = False

    @property
    def met(self):
        return all([d.met for d in self.dependencies])

    @property
    def started(self):
        return all([
            self._started,
            all([d.started for d in self.dependencies])
        ])

    def start(self):
        if self._started is False:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            map(lambda x: x.start(), self.dependencies)
        else:
            self._log.debug('Already started {0}'.format(self))

    def stop(self):
        if self._started is True:
            self._log.debug('Stopping {0}'.format(self))
            self._started = False
            map(lambda x: x.stop(), self.dependencies)
        else:
            self._log.debug('Already stopped {0}'.format(self))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, started={3}, met={4}, '
                'group=[\n\t{5})]'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.started,
                        self.met,
                        '\n\t'.join([str(x) for x in self.dependencies])))

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.dependencies == getattr(other, 'dependencies', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.dependencies != getattr(other, 'dependencies', None)
        ])
