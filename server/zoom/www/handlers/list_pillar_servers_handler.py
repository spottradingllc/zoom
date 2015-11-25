import tornado.ioloop
import tornado.web
import logging
import json

from zoom.common.decorators import TimeThis


class ListPillarServersHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: spot.:rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/v1/pillar/list_servers/ List pillar servers
        @apiVersion 1.0.0
        @apiName GetPilServers
        @apiGroup Pillar
        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            [
                "foo.example.com",
                "bar.example.com"
            ]
        """
        logging.info("Generating list of servers")
        # get all nodes at the root config path
        path = self.application.configuration.pillar_path
        logging.info(path)
        nodes = self.zk.get_children(path)
        self.write(json.dumps(nodes))
