import logging
import os.path

from sentinel.predicate.simple import SimplePredicate
from sentinel.predicate.zkhas_children import ZookeeperHasChildren
from sentinel.util.decorators import connected


class ZookeeperHasGrandChildren(SimplePredicate):
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
        self._children = list()
        self._log = logging.getLogger('sent.{0}.pred.hgc'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    @property
    def met(self):
        return all([d.met for d in self._children])

    def start(self):
        if not self._started:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._walk(self.node)
            for child in self._children:
                child.add_callback(self._callback)
            map(lambda x: x.start(), self._children)
        else:
            self._log.debug('Already started {0}'.format(self))

    def _callback(self):
        for call in self._callbacks:
            self._log.debug('{0}: About to run callback'.format(self))
            call()

    @connected
    def _walk(self, node):
        children = self.zkclient.get_children(node)
        if children:
            for c in children:
                path = '/'.join([node, c])
                self._walk(path)
        else:
            data, stat = self.zkclient.get(node)
            if stat.ephemeralOwner == 0:  # not ephemeral
                self._children.append(ZookeeperHasChildren(self._comp_name,
                                                           self.zkclient,
                                                           node,
                                                           met_on_delete=True,
                                                           parent='zk.has.gc'))
            else:
                self._children.append(
                    ZookeeperHasChildren(self._comp_name,
                                         self.zkclient,
                                         os.path.dirname(node),
                                         met_on_delete=True,
                                         parent='zk.has.gc'))

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
