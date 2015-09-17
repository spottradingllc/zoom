import logging

from kazoo.exceptions import NoNodeError
from zoom.agent.predicate.simple import SimplePredicate
from zoom.common.decorators import connected


class ZookeeperHasChildren(SimplePredicate):
    def __init__(self, comp_name, zkclient, nodepath, ephemeral_only=True,
                 met_on_delete=False, operational=False, new_node_callback=None,
                 parent=None):
        """
        :type comp_name: str
        :type zkclient: kazoo.client.KazooClient
        :type nodepath: str
        :type ephemeral_only: bool
        :type met_on_delete: bool
        :param met_on_delete: Whether we want met to be True when nodepath is
                deleted
        :type operational: bool
        :type new_node_callback: types.FunctionType or None
        :param new_node_callback: This is a special callback used by
                ZookeeperHasGranchildren to keep track of new static nodes
        :type parent: str or None
        """
        SimplePredicate.__init__(self, comp_name, operational=operational, parent=parent)
        self.node = nodepath
        self.zkclient = zkclient
        self._ephemeral_only = ephemeral_only
        self._met_on_delete = met_on_delete
        self._nn_calback = new_node_callback  # currently unused
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
        run_new_node_callback = False
        try:
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
                                else:
                                    self._log.info('New static node detected.')
                                    run_new_node_callback = True

                            except NoNodeError:
                                self._log.debug('Node does not exist: {0}'.format(path))
                                continue
                    else:
                        self.set_met(False)
                else:
                    # TODO: figure out if we need to change this logic for the new node callback
                    self.set_met(bool(children))

                # TODO: this is currently usused. to use it appropriately the logic
                # in _update_children_list of zookeeperhasgrandchildren needs to change
                if run_new_node_callback and self._nn_calback is not None:
                    self._nn_calback()
            else:
                self._handle_node_deletion()
        except NoNodeError:
            self._handle_node_deletion()

    def _handle_node_deletion(self):
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
