import tornado.ioloop
import tornado.web
import logging
import os
import json


class SearchServerHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def get(self, server):
        logging.info('Searching for server {0}'.format(server))
        server = server.upper()
        path = os.path.join(self.application.configuration.agent_configuration_path, server)

        # get tuple (value, ZnodeStat) if the node exists
        if self.zk.exists(path):
            data, stat = self.zk.get(path)
            logging.info('Found server {0}. Outputting XML configuration.'.format(server))

            # write server data
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(data))
        else:
            output = 'Node does not exist.'
            logging.error(output)
            self.write(output)