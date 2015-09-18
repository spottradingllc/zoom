import logging

from zoom.agent.predicate.factory import PredicateFactory
from zoom.agent.entities.stagger_lock import StaggerLock
from zoom.agent.entities.thread_safe_object import ApplicationMode
from zoom.agent.task.task import Task
from zoom.agent.entities.thread_safe_object import ThreadSafeObject


class Action(object):
    def __init__(self, name, component_name, action, xmlpart,
                 staggerpath=None, staggertime=None, mode_controlled=False,
                 action_q=None, zkclient=None, proc_client=None, mode=None,
                 system=None, pred_list=None, settings=None, disabled=False,
                 pd_enabled=True, op_action=None, pd_reason=None,
                 app_state=None):
        """
        :param action: The function to run when all the action's predicates are met
        :param xmlpart: The part of XML pertaining to this Action
        :param mode_controlled: Whether or not the action will run based on the ApplicationMode
        :param op_action: The function to run if this action's operation dependencies go down.
        :type name: str
        :type component_name: str
        :type action: types.FunctionType
        :type xmlpart: xml.etree.ElementTree.Element
        :type staggerpath: str
        :type staggertime: int
        :type mode_controlled: bool
        :type action_q: zoom.agent.entities.unique_queue.UniqueQueue
        :type zkclient: kazoo.client.KazooClient
        :type proc_client: zoom.agent.client.process_client.ProcessClient
        :type mode: zoom.agent.entities.thread_safe_object.ApplicationMode
        :type system: zoom.common.types.PlatformType
        :type pred_list: list
        :type settings: dict
        :type disabled: bool
        :type pd_enabled: bool
        :type op_action: types.FunctionType or None
        :type pd_reason: str or None
        :type app_state: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        """
        self.name = name
        self.disabled = disabled
        self.component_name = component_name
        self._log = logging.getLogger('sent.{0}.act'.format(component_name))
        self._action = action
        self._action_queue = action_q
        self._mode_controlled = mode_controlled
        self._mode = mode
        self._pd_enabled = pd_enabled
        self._op_action = op_action
        self._pd_reason = pd_reason
        self._acquire_lock = ThreadSafeObject(True)

        if staggerpath is not None and staggertime is not None:
            self._stag_lock = StaggerLock(staggerpath, staggertime,
                                          parent=self.component_name,
                                          acquire_lock=self._acquire_lock,
                                          app_state=app_state)
            self._log.info('Using {0}'.format(self._stag_lock))
        else:
            self._stag_lock = None

        factory = PredicateFactory(component_name=component_name,
                                   action=self.name, zkclient=zkclient,
                                   proc_client=proc_client, system=system,
                                   pred_list=pred_list, settings=settings)
        self._predicate = factory.create(xmlpart.find('./Dependency/Predicate'),
                                         callback=self._callback)

    @property
    def ready(self):
        """
        :rtype: bool
        """
        return self._predicate.met

    @property
    def kwargs(self):
        return {
            'action_name': self.name,
            'pd_enabled': self._pd_enabled,
            'pd_reason': self._pd_reason
        }

    @property
    def started(self):
        """
        :rtype: bool
        """
        return self._predicate.started

    @property
    def status(self):
        """
        :rtype: str
        """
        return '{0}:\n  {1}'.format(self, self._predicate)

    def start(self):
        self._log.debug('Starting {0}'.format(self))
        self._predicate.start()

    def stop(self):
        self._predicate.stop()

    def run(self, **kwargs):
        """
        Force run of action (without regard to predicates)
        """
        kwargs.update(self.kwargs)
        self._log.info('Action {0} has been called.'.format(self.name))
        self._execute(**kwargs)

    def _callback(self):
        self._log.info('Callback triggered for {0}:\n{1}'
                       .format(self, self._predicate))

        if self.disabled:
            self._log.info('Not running action {0}. It is disabled.'
                           .format(self.name))
            return
        # ensure all predicates are started
        elif not self.started:
            self._log.warning('All predicates are not started. '
                              'Ignoring action {0}'.format(self.name))
            return
        # ensure all predicates are met
        elif not self._predicate.met:
            self._log.debug('Not triggering action for {0}. '
                            'Predicate not met.'.format(self))

            # check if there are operational dependencies involved.
            # If so, run the operational action. This defaults to 'stop'.
            if self._predicate.operationally_relevant and \
                            self._op_action is not None and \
                    self._mode != ApplicationMode.MANUAL:
                self._log.info('Operational relevancy detected. '
                               'Triggering operation action.')
                self._action_queue.append_unique(Task(self._op_action.__name__,
                                                      func=self._op_action),
                                                 sender=str(self))
            else:
                self._log.debug('Operation dep={0}, Mode={1}'
                                .format(self._predicate.operationally_relevant,
                                        self._mode))
            return

        elif self._action is not None:
            self._log.debug('There is a callback and all predicates are met.')
            if (self._mode != ApplicationMode.MANUAL or
                    not self._mode_controlled):
                self._action_queue.append_unique(Task(self.name,
                                                      func=self._execute,
                                                      kwargs=self.kwargs),
                                                 sender=str(self))
            else:
                self._log.info('Run mode is set to Manual. Not triggering "{0}"'
                               ' action based on dependency change.'
                               .format(self.name))
        else:
            self._log.info('Nothing was done with callback')

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
