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


    @TimeThis(__file__)
    def post(self):
        """
        Save filter
        """
        config_dict = dict()
        comp_id_found = False
        app_state_path = self.configuration._application_state_path + '/'
        agent_config_path = self.configuration._agent_configuration_path[:-1]


        old_path = self.get_argument('oldPath')
        new_path = self.get_argument('newPath')


        old_uid = old_path.replace(app_state_path, '')
        new_uid = new_path.replace(app_state_path, '')

        comp_id_string = 'id="{0}"'.format(old_uid)

        # check if the path exists
        if not self.zk.exists(old_path):
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'Old path does not exist'})
            return

        # check if the new path already exists in ZK
        if self.zk.exists(new_path):
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'New path already exists in Zookeeper'})
            return

        # check if new path has correct base app path
        if app_state_path not in new_path:
            self.set_status(httplib.NOT_FOUND)
            self.write({'errorText': 'New path does not have the correct '
                                     'base app path'})
            return

        children = self.zk.get_children(agent_config_path)

        try:
            for child in children:
                child_path = '/'.join([agent_config_path, child])
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


