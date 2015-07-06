import logging

from kazoo.exceptions import NoNodeError
from zoom.agent.predicate.simple import SimplePredicate
from zoom.common.decorators import connected


class ZookeeperHasChildren(SimplePredicate):
    def __init__(self, comp_name, zkclient, nodepath, ephemeral_only=True,
                 met_on_delete=False, operational=False, parent=None):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type met_on_delete: bool
        :type operational: bool
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, operational=operational, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._ephemeral_only = ephemeral_only
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
        exists = self.zkclient.exists(self.node, watch=self._watch_node)
        if exists:
            children = self.zkclient.get_children(self.node,
                                                  watch=self._watch_node)
            if self._ephemeral_only:
                if children:
                    for c in children:
                        path = '/'.join([self.node, c])
                        try:
                            data, stat = self.zkclient.get(path)
                            # we only care about ephemeral children
                            if stat.ephemeralOwner != 0:
                                self.set_met(True)
                                break
                        except NoNodeError:
                            self._log.debug('Node does not exist: {0}'.format(path))
                            continue
                else:
                    self.set_met(False)
            else:
                self.set_met(bool(children))
        else:
            self._log.warning('Node {0} has been deleted.'.format(self.node))
            if self._met_on_delete:
                self.set_met(True)  # synthetically setting to true
            else:
                self.set_met(False)

    def __repr__(self):
        return ('{0}(component={1}, parent={2}, zkpath={3}, started={4}, '
                'ephemeral_only={5} operational={6}, met={7})'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.node,
                        self.started,
                        self._ephemeral_only,
                        self._operational,
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
