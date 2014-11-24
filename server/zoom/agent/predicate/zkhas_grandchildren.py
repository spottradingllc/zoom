import logging
import os.path

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.zkhas_children \
    import ZookeeperHasChildren
from zoom.common.decorators import connected


class ZookeeperHasGrandChildren(SimplePredicate):
    def __init__(self, comp_name, settings, zkclient, nodepath, parent=None):
        """
        :type comp_name: str
        :type settings: zoom.agent.common.thread_safe_object.ThreadSafeObject
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, settings, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._children = list()
        self._log = logging.getLogger('sent.{0}.pred.hgc'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    @property
    def met(self):
        return all([d.met for d in self._children])

    @property
    def started(self):
        return all([
            self._started,
            all([d.started for d in self._children])
        ])

    def start(self):
        if not self._started:
            self._log.debug('Starting {0}'.format(self))
            self._started = True
            self._rewalk_tree()
        else:
            self._log.debug('Already started {0}'.format(self))

    def _callback(self):
        # TODO: This is the same logic as in SimplePrecicate.
        # We should change it so that we only have to update in one place
        for item in self._callbacks:
            for cb in item.values():
                self._log.debug('{0}: About to run callback.'.format(self))
                cb()

    @connected
    def _walk(self, node):
        """
        Recursively walk a ZooKeeper path and add all children to the _children
            list as ZookeeperHasChildren objects.
        :type node: str
        """
        children = self.zkclient.get_children(node)
        if children:
            for c in children:
                path = '/'.join([node, c])
                self._walk(path)
        else:
            data, stat = self.zkclient.get(node)
            if stat.ephemeralOwner == 0:  # not ephemeral
                self._children.append(
                    ZookeeperHasChildren(self._comp_name,
                                         self._settings,
                                         self.zkclient,
                                         node,
                                         met_on_delete=True,
                                         parent='zk.has.gc'))
            else:
                self._children.append(
                    ZookeeperHasChildren(self._comp_name,
                                         self._settings,
                                         self.zkclient,
                                         os.path.dirname(node),
                                         met_on_delete=True,
                                         parent='zk.has.gc'))

    @connected
    def _rewalk_tree(self, event=None):
        """
        Clear children list and rewalk the tree starting at self.node.
        If the node does not exist, set a watch.
        When the node is created the watch will trigger the recursive walk.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        if self.zkclient.exists(self.node, watch=self._rewalk_tree):
            del self._children[:]  # clear children list
            self._walk(self.node)
            for child in self._children:
                child.add_callback({"zk_hgc": self._callback})
            map(lambda x: x.start(), self._children)
        else:
            self._children.append(self._create_dummy_predicate())
            self._log.warning('Node {0} does not exist. Will wait until it '
                              'does.'.format(self.node))

    def _create_dummy_predicate(self):
        # TODO: This is duplicate code (available in PredicateFactory)
        """
        This is a placeholder for when the path the ZKHGC is given a path
            that doesn't exist
        This will ensure that while the path doesn't exist, self.met
            returns False.
        :rtype: zoom.agent.predicate.simple.SimplePredicate
        """
        dummy = SimplePredicate(self._comp_name,
                                self._settings,
                                parent=self._parent)
        dummy.set_met(False)
        return dummy

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
