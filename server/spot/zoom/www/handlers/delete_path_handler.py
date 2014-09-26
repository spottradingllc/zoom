import logging
import tornado.web

from httplib import NOT_ACCEPTABLE

from spot.zoom.www.utils.decorators import TimeThis


class DeletePathHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        return self.application.configuration

    @TimeThis(__file__)
    def post(self):
        """
        Save filter
        """
        login_name = self.get_argument("loginName")
        path = self.get_argument("delete")
        logging.info("Recieved delete request from {0} for path {1}"
                     .format(login_name, path))
        if self.application.zk.get_children(path):
            warn = "Path {} has children, not deleting!".format(path)
            logging.warn(warn)
            self.set_status(NOT_ACCEPTABLE)
            self.write(warn)
        else:
            self.application.zk.delete(path)
