import logging
import tornado.web
import re
import httplib

from zoom.common.decorators import TimeThis


class ToolsRefactorPathHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @property
    def configuration(self):
        return self.application._configuration

    @property
    def app_state_path(self):
        return self.configuration._application_state_path + '/'

    @property
    def agent_config_path(self):
        return 'justin/agent'
        # return self.configuration._agent_configuration_path[:-1]

    @property
    def old_path(self):
        logging.info('Whats the old path')
        return self.get_argument('oldPath')

    @property
    def new_path(self):
        return self.get_argument('newPath')

    @TimeThis(__file__)
    def post(self):
        """
        Save filter
        """
        # check if the path exists
        if not self.zk.exists(self.old_path):
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'Old path does not exist'})
            return
        #if the old path has children or not
        children = self.zk.get_children(self.old_path)
        if not children:
            self._test_partial_path_refactor()
        else:
            # Take the first child and check if its ephemeral or not
            child_path = '{0}/{1}'.format(self.old_path, children[0])
            data, stats = self.zk.get(child_path)
            if stats.owner_session_id in (0, None):
                self._test_partial_path_refactor()
            else:
                self._test_full_path_refactor()

    def _test_partial_path_refactor(self):
        self._refactor_paths()

    def _test_full_path_refactor(self):
        # check if the new path already exists in ZK
        if self.zk.exists(self.new_path):
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'New path already exists in Zookeeper'})
            return

        # check if new path has correct base app path
        if self.app_state_path not in self.new_path:
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'New path does not have the correct '
                                     'base app path'})
            return

        self._refactor_paths()

    def _refactor_paths(self):
        config_dict = dict()
        comp_id_found = False
        old_uid = self.old_path.replace(self.app_state_path, '')
        new_uid = self.new_path.replace(self.app_state_path, '')
        comp_id_string = 'id="{0}"'.format(old_uid)

        # Getting all config children
        children = self.zk.get_children(self.agent_config_path)

        try:
            for child in children:
                child_path = '/'.join([self.agent_config_path, child])
                data, stat = self.zk.get(child_path)
                if old_uid in data:
                    updated_data, num = re.subn(old_uid, new_uid, data)
                    config_dict[child_path] = str(updated_data)
                    #check if the comp_id string exists in any configs
                    if comp_id_string in data:
                        comp_id_found = True

            if comp_id_found:
                # push the new configs to Zookeeper
                for child_path, config in config_dict.iteritems():
                    self.zk.set(child_path, config)
                logging.info('Added new configs for paths: {0}'
                             .format(config_dict.keys()))
                self.write({'config_dict': config_dict.keys()})
                return
            else:
                self.set_status(httplib.NOT_FOUND)
                self.write({'errorText': 'Old path doesn\'t have valid component id'})
                return
        except Exception as e:
            logging.info('Exception in Refactor Path Handler: {0}'.format(e))



