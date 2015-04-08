import logging
from xml.etree import ElementTree

from zoom.agent.action.action import Action
from zoom.agent.util.helpers import verify_attribute
from zoom.common.decorators import catch_exception


class ActionFactory(object):
    def __init__(self, component=None, zkclient=None, proc_client=None,
                 action_queue=None, mode=None, system=None, pred_list=None,
                 app_state=None, settings=None):
        """
        :type component: zoom.agent.entities.application.Application
        :type zkclient: kazoo.client.KazooClient or None
        :type proc_client: zoom.agent.client.process_client.ProcessClient
        :type action_queue: zoom.agent.entities.unique_queue.UniqueQueue
        :type mode: zoom.agent.entities.thread_safe_object.ApplicationMode
        :type system: zoom.common.types.PlatformType
        :type pred_list: list
        :type app_state: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        """
        self._zk = zkclient
        self._proc = proc_client
        self._comp = component
        self._action_q = action_queue
        self._mode = mode
        self._system = system
        self._pred_list = pred_list
        self._app_state = app_state
        self._settings = settings
        self._log = logging.getLogger('sent.{0}.act.factory'
                                      .format(self._comp.name))

    @catch_exception(Exception)
    def create(self, xmlpart):
        """
        :type xmlpart: xml.etree.ElementTree.Element
        :rtype: dict
        """
        if isinstance(xmlpart, str):
            root = ElementTree.fromstring(xmlpart)
        else:
            root = xmlpart

        actions = dict()
        for element in root.iter('Action'):
            func = verify_attribute(element, 'func', none_allowed=True)
            op_func = verify_attribute(element, 'op_func', none_allowed=True)
            name = verify_attribute(element, 'id').lower()
            staggerpath = verify_attribute(element, 'staggerpath',
                                           none_allowed=True)
            staggertime = verify_attribute(element, 'staggertime',
                                           none_allowed=True, cast=int)
            mode_controlled = verify_attribute(element, 'mode_controlled',
                                               none_allowed=True)
            disabled = verify_attribute(element, 'disabled', none_allowed=True)
            pd_enabled = verify_attribute(element, 'pd_enabled',
                                          none_allowed=True)
            pd_reason = verify_attribute(element, 'pd_reason',
                                         none_allowed=True)

            if pd_enabled is None:
                pagerduty_enabled = True
            else:
                pagerduty_enabled = pd_enabled

            if func is not None:
                action = getattr(self._comp, func, None)
            else:
                action = getattr(self._comp, name, None)

            if op_func is None:
                # default operational dependency action to 'stop'
                op_action = getattr(self._comp, 'stop', None)
            else:
                op_action = getattr(self._comp, op_func, None)

            if action is not None:
                actions[name] = Action(name, self._comp.name, action, element,
                                       action_q=self._action_q,
                                       staggerpath=staggerpath,
                                       staggertime=staggertime,
                                       mode_controlled=mode_controlled,
                                       zkclient=self._zk,
                                       proc_client=self._proc,
                                       mode=self._mode,
                                       system=self._system,
                                       pred_list=self._pred_list,
                                       settings=self._settings,
                                       disabled=bool(disabled),
                                       pd_enabled=pagerduty_enabled,
                                       pd_reason=pd_reason,
                                       op_action=op_action,
                                       app_state=self._app_state)
                self._log.info('Registered {0}.'.format(actions[name]))
            else:
                self._log.error('Invalid action ID or func specified: '
                                'ID: {0}, func: {1}'.format(name, func))


        return actions