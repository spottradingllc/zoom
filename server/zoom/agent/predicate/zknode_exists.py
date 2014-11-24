import logging

from zoom.agent.predicate.simple import SimplePredicate
from zoom.common.decorators import connected


class ZookeeperNodeExists(SimplePredicate):
    def __init__(self, comp_name, settings, zkclient, nodepath, parent=None):
        """
        :type comp_name: str
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._log = logging.getLogger('sent.{0}.pred.ne'.format(comp_name))
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
        exists = self.zkclient.exists(self.node, watch=self._watch_node)
        self.set_met(bool(exists))

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, zkpath={3}, started={4}, '
                'met={5})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.node,
                        self.started,
                        self.met))
    
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
