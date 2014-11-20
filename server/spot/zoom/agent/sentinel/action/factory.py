import logging
from xml.etree import ElementTree

from spot.zoom.agent.sentinel.action.action import Action
from spot.zoom.agent.sentinel.util.helpers import verify_attribute
from spot.zoom.common.decorators import catch_exception


class ActionFactory(object):
    def __init__(self, component=None, zkclient=None, proc_client=None,
                 action_queue=None, mode=None, system=None, pred_list=None,
                 settings=None):
        """
        :type component: spot.zoom.agent.sentinel.common.application.Application
        :type zkclient: kazoo.client.KazooClient or None
        :type proc_client: spot.zoom.agent.sentinel.client.process_client.ProcessClient
        :type action_queue: spot.zoom.agent.sentinel.common.unique_queue.UniqueQueue
        :type mode: spot.zoom.agent.sentinel.common.thread_safe_object.ApplicationMode
        :type system: spot.zoom.common.types.PlatformType
        :type pred_list: list
        :type settings: spot.zoom.agent.sentinel.common.thread_safe_object.ThreadSafeObject
        """
        self._zk = zkclient
        self._proc = proc_client
        self._comp = component
        self._action_q = action_queue
        self._mode = mode
        self._system = system
        self._pred_list = pred_list
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
            if pd_enabled is None:
                pagerduty_enabled = True
            else:
                pagerduty_enabled = pd_enabled

            action = getattr(self._comp, name, None)
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
                                   pd_enabled=pagerduty_enabled)
            self._log.info('Registered {0}.'.format(actions[name]))

        return actions
