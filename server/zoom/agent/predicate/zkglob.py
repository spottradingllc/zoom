import fnmatch
import logging
import os.path
from kazoo.exceptions import NoNodeError
from zoom.common.decorators import connected, catch_exception
from zoom.agent.predicate.zkhas_grandchildren import ZookeeperHasGrandChildren
from zoom.agent.util.helpers import zk_path_join


class ZookeeperGlob(ZookeeperHasGrandChildren):
    def __init__(self, comp_name, zkclient, nodepattern,
                 ephemeral_only=True, operational=False, parent=None):
        """
        Predicate for watching Zookeeper nodes using unix-style glob matching.

        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepattern: str
        :type operational: bool
        :type parent: str or None
        """
        self.nodepattern = nodepattern
        self.node = self._get_deepest_non_glob_start(nodepattern)
        ZookeeperHasGrandChildren.__init__(self, comp_name, zkclient, self.node,
                                           ephemeral_only=ephemeral_only,
                                           operational=operational,
                                           parent=parent)

        self._log = logging.getLogger('sent.{0}.pred.glob'.format(comp_name))
        self._log.info('Registered {0}'.format(self))

    @catch_exception(NoNodeError, msg='A node has been removed during walk.')
    @connected
    def _walk(self, node, node_list):
        """
        Recursively walk a ZooKeeper path and add all children to the _children
            list as ZookeeperHasChildren objects.
        :type node: str
        """
        children = self.zkclient.get_children(node, watch=self._rewalk_tree)
        if children:
            for c in children:
                path = zk_path_join(node, c)
                self._walk(path, node_list)
        else:
            data, stat = self.zkclient.get(node)
            if stat.ephemeralOwner == 0:  # not ephemeral
                if fnmatch.fnmatch(node, self.nodepattern):
                    node_list.append(node)
            else:
                if fnmatch.fnmatch(os.path.dirname(node), self.nodepattern):
                    node_list.append(os.path.dirname(node))

    def _get_deepest_non_glob_start(self, p):
        if "*" in p:
            s = p.split('*')
            return s[0].rstrip('/')
        else:
            return p

    def __repr__(self):
        indent_count = len(self._parent.split('/'))
        indent = '\n' + '    ' * indent_count
        return ('{0}(component={1}, parent={2}, glob_pattern={3}, started={4}, '
                'operational={5}, met={6}, group=[{7}{8}]))'
                .format(self.__class__.__name__,
                        self._comp_name,
                        self._parent,
                        self.nodepattern,
                        self.started,
                        self._operational,
                        self.met,
                        indent,
                        indent.join([str(x) for x in self._children])))
