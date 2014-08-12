import logging

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate
from spot.zoom.agent.sentinel.util.decorators import connected


class ZookeeperHasChildren(SimplePredicate):
    def __init__(self, comp_name, zkclient, nodepath, met_on_delete=False,
                 parent=None):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type met_on_delete: bool
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._met_on_delete = met_on_delete
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
        else:
            self._log.warning('Node {0} has been deleted.'.format(self.node))
            if self._met_on_delete:
                self.set_met(True)  # synthetically setting to true

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
