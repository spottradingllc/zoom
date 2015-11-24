import tornado.ioloop
import tornado.web
import logging
import json

from zoom.common.decorators import TimeThis


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
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/v1/config/list_servers/ List sentinel servers
        @apiVersion 1.0.0
        @apiName ListSentServers
        @apiGroup Sentinel Config
        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            [
                "foo.example.com",
                "bar.example.com"
            ]
        """
        logging.info('Generating list of nodes')

        # get all nodes at the root config path
        nodes = self.zk.get_children(self.agent_configuration_path)
        self.write(json.dumps(nodes))
