import logging

from source.predicate.simple import SimplePredicate
from source.util.decorators import connected


class ZookeeperHasChildren(SimplePredicate):
    def __init__(self, comp_name, zkclient, nodepath, parent=None):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._log = logging.getLogger('sent.{0}.pred.hc'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    def start(self):
        if not self._started:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._watch_node()
        else:
            self._log.debug('Already started {0}'.format(self))

    @connected
    def _watch_node(self, event=None):
        """
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        children = list()
        exists = self.zkclient.exists(self.node, watch=self._watch_node)
        if exists:
            try:
                children = self.zkclient.get_children(self.node,
                                                      watch=self._watch_node)
            finally:
                self.set_met(bool(children))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, zkpath={3}, met={4})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.node,
                        self.met)
                )

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.node == getattr(other, 'node', None)
        ])

    def __ne__(self, other):
        return any([
            type(self) != type(other),
            self.node != getattr(other, 'node', None)
        ])