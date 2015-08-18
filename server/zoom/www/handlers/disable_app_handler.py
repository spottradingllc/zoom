import logging
import httplib
import os.path
from xml.etree import ElementTree
from tornado.web import RequestHandler

from zoom.common.decorators import TimeThis


class DisableAppHandler(RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @property
    def agent_config_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.agent_configuration_path

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/disable Enable/Disable Zoom startup for an application
        @apiParam {String} host The user that submitted the task
        @apiParam {String} id The application id to disable/enable
        @apiParam {Boolean} Whether to disable Zoom startup
        @apiVersion 1.0.0
        @apiName DisableApp
        @apiGroup DisableApp
        """
        try:
            user = self.get_argument('user')
            component_id = self.get_argument("id")
            host = self.get_argument("host")
            disable = self.get_argument("disable")
            logging.info('User: {0}, App: {1}, Disable: {2}'
                         .format(user, component_id, disable))

            path = os.path.join(self.agent_config_path, host)
            update = False

            if self.zk.exists(path):
                data, stat = self.zk.get(path)
                config = ElementTree.fromstring(data)
                for component in config.iter('Component'):
                    cid = component.attrib.get('id')
                    if cid == component_id:
                        update = True
                        for action in component.iter('Action'):
                            aid = action.attrib.get('id')
                            if aid not in ('register', 'unregister'):
                                action.attrib['disabled'] = disable
                                logging.info('{0}abled {1}:{2}'.format(('Dis' if disable else 'En'), cid, aid))

                if update:
                    self.zk.set(path, ElementTree.tostring(config))

            else:
                self.set_status(httplib.NOT_FOUND)
                self.write('Could not find {0} on host {1}'.format(component_id, host))

        except Exception as e:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.write(str(e))
            logging.exception(e)
