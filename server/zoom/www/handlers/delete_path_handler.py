import logging
import tornado.web

from zoom.common.decorators import TimeThis


class DeletePathHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/delete/ Delete path in Zookeeper
        @apiParam {String} login_user The user that submitted the task
        @apiParam {String} delete The Zookeeper path to delete
        @apiVersion 1.0.0
        @apiName DeletePath
        @apiGroup DeletePath
        """
        login_name = self.get_argument("loginName")
        path = self.get_argument("delete")
        logging.info("Recieved delete request from {0}:({1}) for path {2}"
                     .format(login_name, self.request.remote_ip, path))
        self.zk.delete(path)