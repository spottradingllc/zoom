import logging
import tornado.web

from zoom.common.decorators import TimeThis


class DeletePathHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @property
    def app_state_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.application_state_path

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/v1/delete/ Delete path in Zookeeper
        @apiParam {String} login_user The user that submitted the task
        @apiParam {String} delete The Zookeeper path to delete
        @apiVersion 1.0.0
        @apiName DeletePath
        @apiGroup DeletePath
        """
        login_name = self.get_argument("loginName")
        path = self.get_argument("delete")
        split_path = path.split('/')
        scounter = len(split_path)
        while scounter != 0:
            new_path = '/'.join(split_path[0:scounter])
            if new_path == self.app_state_path:
                break
            elif not self.zk.get_children(new_path):
                self.zk.delete(new_path)
                logging.info("Delete initiated by user {0} for path {1}"
                             .format(login_name, new_path))
            else:
                break
            scounter -= 1
