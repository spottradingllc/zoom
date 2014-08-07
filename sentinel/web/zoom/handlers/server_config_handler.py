import json
import logging
import os
import tornado.ioloop
import tornado.web

from kazoo.exceptions import NoNodeError
from zoom.utils.decorators import timethis


class ServerConfigHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk

    @timethis(__file__)
    def put(self, server):
        logging.info('Updating server {0}'.format(server))
        server = server.upper()
        zk_path = os.path.join(
            self.application.configuration.agent_configuration_path, server)

        try:
            request = json.loads(self.request.body)
            # get XML data from JSON dictionary
            data = request.get("XML")
            logging.info('Received XML configuration for {0}'.format(server))

            self.zk.set(zk_path, str(data))
            self.write('Node successfully updated.')
            logging.info('Updated server {0}'.format(server))

        except NoNodeError:
            output = 'Node does {0} not exist.'.format(zk_path)
            logging.exception(output)
            self.write(output)

    @timethis(__file__)
    def get(self, server):
        logging.info('Searching for server {0}'.format(server))
        server = server.upper()
        path = os.path.join(
            self.application.configuration.agent_configuration_path, server)

        # get tuple (value, ZnodeStat) if the node exists
        if self.zk.exists(path):
            data, stat = self.zk.get(path)
            logging.info('Found server {0}. '
                         'Outputting XML configuration.'.format(server))

            # write server data
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(data))
        else:
            output = 'Node does not exist.'
            logging.error(output)
            self.write(output)

    @timethis(__file__)
    def post(self, server):
        logging.info('Adding server {0}'.format(server))
        server = server.upper()
        path = os.path.join(
            self.application.configuration.agent_configuration_path, server)

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
                output = 'Parent nodes are missing for {0}'.format(path)
                self.write(output)
                logging.info(output)

    @timethis(__file__)
    def delete(self, server):
        logging.info('Deleting server {0}'.format(server))
        server = server.upper()
        path = os.path.join(
            self.application.configuration.agent_configuration_path, server)

        # recursively delete server and children
        try:
            self.zk.delete(path)
            self.write('Node successfully deleted.')
            logging.info('Deleted {0}'.format(server))
        except NoNodeError:
            output = 'Node {0} does not exist.'.format(path)
            logging.error(output)
            self.write(output)
