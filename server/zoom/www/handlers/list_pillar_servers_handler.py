import tornado.ioloop
import tornado.web
import logging
import json

from zoom.common.decorators import TimeThis


class ListPillarServersHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self):
        logging.info("Generating list of servers")
        # get all nodes at the root config path
        path = self.application.configuration.pillar_path
        logging.info(path)
        nodes = self.zk.get_children(path)
        self.write(json.dumps(nodes))
