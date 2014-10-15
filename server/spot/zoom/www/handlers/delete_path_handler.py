import logging
import tornado.web

from httplib import NOT_ACCEPTABLE

from spot.zoom.common.decorators import TimeThis


class DeletePathHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def post(self):
        """
        Save filter
        """
        login_name = self.get_argument("loginName")
        path = self.get_argument("delete")
        logging.info("Recieved delete request from {0}:({1}) for path {2}"
                     .format(login_name, self.request.remote_ip, path))
        if self.zk.get_children(path):
            warn = "Path {} has children, not deleting!".format(path)
            logging.warn(warn)
            self.set_status(NOT_ACCEPTABLE)
            self.write(warn)
        else:
            self.zk.delete(path)
