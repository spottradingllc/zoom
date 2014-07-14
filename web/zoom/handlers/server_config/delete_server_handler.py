import tornado.ioloop
import tornado.web
import logging
import os

from kazoo.exceptions import NoNodeError


class DeleteServerHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def get(self, server):
        logging.info('Deleting server {0}'.format(server))
        server = server.upper()
        path = os.path.join(self.application.configuration.agent_configuration_path, server)

        # recursively delete server and children
        try:
            self.zk.delete(path)
            self.write('Node successfully deleted.')
            logging.info('Deleted {0}'.format(server))
        except NoNodeError:
            output = 'Node {0} does not exist.'.format(path)
            logging.error(output)
            self.write(output)