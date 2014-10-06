import tornado.ioloop
import tornado.web
import logging
import json

from spot.zoom.common.decorators import TimeThis


class ListServersHandler(tornado.web.RequestHandler):
    @property
    def agent_configuration_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.agent_configuration_path

    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self):
        logging.info('Generating list of nodes')

        # get all nodes at the root config path
        nodes = self.zk.get_children(self.agent_configuration_path)
        self.write(json.dumps(nodes))
