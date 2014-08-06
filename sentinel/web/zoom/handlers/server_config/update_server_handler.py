import tornado.ioloop
import tornado.web
import logging
import os

from kazoo.exceptions import NoNodeError


class UpdateServerHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def post(self, server):
        logging.info('Updating server {0}'.format(server))
        server = server.upper()
        zk_path = os.path.join(self.application.configuration.agent_configuration_path, server)

        # get XML data from JSON dictionary
        data = self.get_argument("XML")
        logging.info('Received XML configuration for {0}'.format(server))

        try:
            self.zk.set(zk_path, str(data))
            self.write('Node successfully updated.')
            logging.info('Updated server {0}'.format(server))

        except NoNodeError:
            output = 'Node does {0} not exist.'.format(zk_path)
            logging.error(output)
            self.write(output)
