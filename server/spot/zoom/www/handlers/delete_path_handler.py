import logging
import tornado.web

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
        self.zk.delete(path)