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

    @TimeThis(__file__)
    def post(self):
        """
        Save filter
        """
        config_path = '/justin/configs'
        app_state_path = '/spot/software/state/application/'
        updated_server_list = list()

        old_path = self.get_argument('oldPath')
        new_path = self.get_argument('newPath')

        old_unique_id = old_path.replace(app_state_path, '')
        new_unique_id = new_path.replace(app_state_path, '')

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
            self.write({'errorText': 'New path does not have the correct base app path'})
            return


        children = self.zk.get_children(config_path)

        for child in children:
            child_path = '/'.join([config_path, child])
            data, stat = self.zk.get(child_path)
            if old_unique_id in data:
                updated_data, num = re.subn(old_unique_id, new_unique_id, data)
                updated_server_list.append(child)
                # push update_data to Zookeeper
            else:
                logging.info('### Skipping')

        self.write({'server_list': updated_server_list})
