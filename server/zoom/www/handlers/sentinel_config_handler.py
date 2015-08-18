import json
import logging
import tornado.ioloop
import tornado.web

from xml.etree import ElementTree
from kazoo.exceptions import NoNodeError

from zoom.common.decorators import TimeThis
from zoom.agent.util.helpers import zk_path_join


class SentinelConfigHandler(tornado.web.RequestHandler):
    @property
    def agent_configuration_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.agent_configuration_path

    @property
    def app_state_cache(self):
        """
        :rtype: zoom.messages.application_states.ApplicationStatesMessage
        """
        return self.application.data_store.load_application_state_cache()

    @property
    def zk(self):
        """
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def put(self, server):
        """
        @api {put} /api/config/:host Create|Update sentinel config
        @apiVersion 1.0.0
        @apiName UpdateSentinel
        @apiGroup Sentinel Config
        """
        logging.info('Updating server {0} for client {1}'
                     .format(server, self.request.remote_ip))
        zk_path = zk_path_join(self.agent_configuration_path, server)

        try:
            request = json.loads(self.request.body)
            # get XML data from JSON dictionary
            data = request.get("XML")
            logging.info('Received XML configuration for {0}'.format(server))

            if not self.zk.exists(zk_path):
                self.zk.create(zk_path)

            if not self._is_valid(str(data), server):
                logging.warning('Not updating invalid config for server: {0}'
                                .format(server))
            else:
                self.zk.set(zk_path, str(data))
                self.write('Node successfully updated.')
                logging.info('Updated server {0}'.format(server))

        except NoNodeError:
            output = 'Node does {0} not exist.'.format(zk_path)
            logging.exception(output)
            self.write(output)

    @TimeThis(__file__)
    def get(self, server):
        """
        @api {get} /api/config/:host Get sentinel config for server
        @apiVersion 1.0.0
        @apiName GetSentinel
        @apiGroup Sentinel Config
        """
        logging.info('Searching for server {0}'.format(server))
        path = zk_path_join(self.agent_configuration_path, server)

        # get tuple (value, ZnodeStat) if the node exists
        if self.zk.exists(path):
            data, stat = self.zk.get(path)
            logging.info('Found server {0}. '
                         'Outputting XML configuration.'.format(server))

            # write server data
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(data))
        else:
            output = 'Node does not exist.'
            logging.error(output)
            self.write(output)

    @TimeThis(__file__)
    def post(self, server):
        """
        @api {post} /api/config/:host Create sentinel config
        @apiParam {String} XML A string containing the XML of the Sentinel Config
        @apiVersion 1.0.0
        @apiName CreateSentinel
        @apiGroup Sentinel Config
        """
        logging.info('Adding server {0} for client {1}'
                     .format(server, self.request.remote_ip))
        path = zk_path_join(self.agent_configuration_path, server)

        # add server if it does not already exist
        if self.zk.exists(path):
            output = 'Node {0} already exists'.format(server)
            logging.info(output)
        else:
            # get XML data from JSON dictionary
            data = self.get_argument("XML")
            logging.info('Received XML configuration for {0}'.format(server))
            try:
                self.zk.create(path, bytes(data))
                self.write('Node successfully added.')
                logging.info('Added {0}'.format(server))
            except NoNodeError:
                output = 'Parent nodes are missing for {0}'.format(path)
                self.write(output)
                logging.info(output)

    @TimeThis(__file__)
    def delete(self, server):
        """
        @api {put} /api/config/:host Delete sentinel config
        @apiVersion 1.0.0
        @apiName DeleteSentinel
        @apiGroup Sentinel Config
        """
        logging.info('Deleting server {0} for client'
                     .format(server, self.request.remote_ip))
        path = zk_path_join(self.agent_configuration_path, server)

        # recursively delete server and children
        try:
            self.zk.delete(path)
            self.write('Node successfully deleted.')
            logging.info('Deleted {0}'.format(server))
        except NoNodeError:
            output = 'Node {0} does not exist.'.format(path)
            logging.error(output)
            self.write(output)

    def _is_valid(self, xmlstring, server):
        """
        Test submitted config against cached data in ApplicationStateCache to
        see whether the submitted IDs/registration paths are the same. If they
        are and the server is different, return False.

        :type xmlstring: str
        :type server: str
        :rtype: bool
        """
        valid = True

        config = ElementTree.fromstring(xmlstring)
        for component in config.iter('Component'):
            if not valid:
                break
            for app in self.app_state_cache.application_states.values():
                app_host = app.get('application_host')
                app_name = app.get('application_name')
                app_reg_path = app.get('configuration_path')
                reg_path = component.get('registrationpath', None)

                if reg_path is not None:
                    if reg_path == app_reg_path and server != app_host:
                        if self._double_check_config(app_host,
                                                     reg_to_find=reg_path):
                            valid = False
                            self.write(
                                'Config is not valid! Registration path {0} '
                                'matches existing config on server {1}.'
                                 .format(reg_path, app_host))
                        break

                else:
                    comp_id = component.get('id')
                    if comp_id == app_name and server != app_host:
                        if self._double_check_config(app_host,
                                                     id_to_find=comp_id):
                            valid = False
                            self.write('Config is not valid! Component ID {0} '
                                       'matches existing config on server {1}.'
                                       .format(comp_id, app_host))
                        break

        return valid

    def _double_check_config(self, server, id_to_find=None, reg_to_find=None):
        """
        It is possible that the ApplicationStateCache will have a stale host
        value. Check the actual config to make sure the component_id is REALLY
        there.
        :type server: str
        :type id_to_find: str or None
        :type reg_to_find: str or None
        :rtype: bool
        """
        path = zk_path_join(self.agent_configuration_path, server)
        if self.zk.exists(path):
            xmlstr, stat = self.zk.get(path)
        else:
            return False

        config = ElementTree.fromstring(xmlstr)
        for component in config.iter('Component'):
            comp_id = component.get('id')
            comp_reg_path = component.get('registrationpath')
            if id_to_find and id_to_find == comp_id:
                return True
            elif reg_to_find and reg_to_find == comp_reg_path:
                return True

        return False
