import logging
from sentinel.predicate.simple import SimplePredicate


class PredicateOr(SimplePredicate):
    def __init__(self, comp_name, predicates, parent=None):
        """
        :type comp_name: str
        :type predicates: list of sentinel.common.predicate objects
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, parent=parent)
        self.dependencies = predicates
        self._log = logging.getLogger('sent.{0}.pred.or'.format(comp_name))
        self._log.info('Registered {0}'.format(self))
        self._started = False

    @property
    def met(self):
        return any([d.met for d in self.dependencies])

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
        return ('{0}(component={1}, parent={2}, met={3}, group=[\n\t{4})]'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.met,
                        '\n\t'.join([str(x) for x in self.dependencies])
                        )
                )

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
