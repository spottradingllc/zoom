import tornado.ioloop
import tornado.web
import logging
import os

from kazoo.exceptions import NoNodeError


class AddServerHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def post(self, server):
        logging.info('Adding server {0}'.format(server))
        server = server.upper()
        path = os.path.join(self.application.configuration.agent_configuration_path, server)

        # add server if it does not already exist
        if self.zk.exists(path):
            output = 'Node {0} already exists'.format(server)
            logging.info(output)
        else:
            # get XML data from JSON dictionary
            data = self.get_argument("XML")
            logging.info('Received XML configuration for {0}'.format(server))
            try:
                self.zk.create(path, bytes(data))
                self.write('Node successfully added.')
                logging.info('Added {0}'.format(server))
            except NoNodeError:
                output = 'Parent nodes are missing.'
                self.write(output)
                logging.info(output)
