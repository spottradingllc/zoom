import tornado.ioloop
import tornado.web
import logging
import json


class ListServersHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def get(self):
        logging.info('Generating list of nodes')
        path = self.application.configuration.agent_configuration_path

        # get all nodes at the root config path
        nodes = self.zk.get_children(path)
        self.write(json.dumps(nodes))

