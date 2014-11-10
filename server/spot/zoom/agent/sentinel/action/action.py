import logging

from spot.zoom.agent.sentinel.predicate.factory import PredicateFactory
from spot.zoom.agent.sentinel.common.stagger_lock import StaggerLock
from spot.zoom.agent.sentinel.common.thread_safe_object import ApplicationMode
from spot.zoom.agent.sentinel.common.task import Task
from spot.zoom.agent.sentinel.common.thread_safe_object import ThreadSafeObject


class Action(object):
    def __init__(self, name, component_name, action, xmlpart,
                 staggerpath=None, staggertime=None, mode_controlled=False,
                 action_q=None, zkclient=None, proc_client=None, mode=None,
                 system=None, pred_list=None, settings=None, disabled=False):
        """
        :type name: str
        :type component_name: str
        :type action: func
        :type xmlpart: xml.etree.ElementTree.Element
        :type staggerpath: str
        :type staggertime: int
        :param mode_controlled: Whether or not the action will run based on the
                                ApplicationMode
        :type mode_controlled: bool
        :type action_q: spot.zoom.agent.sentinel.common.unique_queue.UniqueQueue
        :type zkclient: kazoo.client.KazooClient
        :type proc_client: spot.zoom.agent.sentinel.client.process_client.ProcessClient
        :type mode: spot.zoom.agent.sentinel.common.thread_safe_object.ApplicationMode
        :type system: spot.zoom.common.types.PlatformType
        :type pred_list: list
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        :type disabled: bool
        """
        self.name = name
        self._log = logging.getLogger('sent.{0}.act'.format(component_name))
        self.component_name = component_name
        self._action = action
        self._action_queue = action_q
        self._mode_controlled = mode_controlled
        self._mode = mode
        self._disabled = disabled
        self._acquire_lock = ThreadSafeObject(True)

        if staggerpath is not None and staggertime is not None:
            self._stag_lock = StaggerLock(staggerpath, staggertime,
                                          parent=self.component_name,
                                          acquire_lock=self._acquire_lock)
            self._log.info('Using {0}'.format(self._stag_lock))
        else:
            self._stag_lock = None

        factory = PredicateFactory(component_name=component_name,
                                   parent=self.name, zkclient=zkclient,
                                   proc_client=proc_client, system=system,
                                   pred_list=pred_list, settings=settings)
        self._predicate = factory.create(xmlpart.find('./Dependency/Predicate'),
                                         callback=self._callback)

    @property
    def ready(self):
        return self._predicate.met

    def start(self):
        self._log.debug('Starting {0}'.format(self))
        self._predicate.start()

    def stop(self):
        self._predicate.stop()

    def run(self, **kwargs):
        """
        Force run of action (without regard to predicates)
        """
        self._log.info('Action {0} has been called.'.format(self.name))
        self._execute(**kwargs)

    def _callback(self):
        self._log.info('Callback triggered for {0}:\n{1}'
                       .format(self, self._predicate))

        if self._disabled:
            self._log.info('Not running action {0}. It is disabled.'
                           .format(self.name))
            return
        # ensure all predicates are started
        elif not self._predicate.started:
            self._log.warning('All predicates are not started. '
                              'Ignoring action {0}'.format(self.name))
            return
        # ensure all predicates are met
        elif not self._predicate.met:
            self._log.debug('Not triggering action for {0}. '
                            'Predicate not met.'.format(self))
            return

        elif self._action is not None:
            self._log.debug('There is a callback and all predicates are met.')
            if (self._mode != ApplicationMode.MANUAL or
                    not self._mode_controlled):
                self._action_queue.append_unique(Task(self.name,
                                                      func=self._execute),
                                                 sender=str(self))
            else:
                self._log.info('Run mode is set to Manual. Not triggering "{0}"'
                               ' action based on dependency change.'
                               .format(self.name))

    def _execute(self, **kwargs):
        self._log.info('Attempting action "{0}"'.format(self.name))
        if self._stag_lock is not None:
            self._stag_lock.start()
            self._action(**kwargs)
            self._stag_lock.join()
        else:
            self._action(**kwargs)

    def __repr__(self):
        return 'Action(name={0}, component={1})'.format(self.name,
                                                        self.component_name)

    def __str__(self):
        return self.__repr__()
