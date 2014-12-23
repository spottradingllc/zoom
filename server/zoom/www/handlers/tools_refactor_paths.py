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
        updated_server_list = list()

        old_path = self.get_argument('oldPath')
        new_path = self.get_argument('newPath')

        # check if the path exists
        if not self.zk.exists(old_path) or new_path is None:
            self.set_status(httplib.NOT_FOUND)
            return

        children = self.zk.get_children(config_path)

        for child in children:
            child_path = '/'.join([config_path, child])
            data, stat = self.zk.get(child_path)
            if old_path in data:
                updated_data, num = re.subn(old_path, new_path, data)
                updated_server_list.append(child)
            else:
                logging.info('### Skipping')

        self.write({'server_list': updated_server_list})
