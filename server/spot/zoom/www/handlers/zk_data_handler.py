import logging
import tornado.ioloop
import tornado.web

from spot.zoom.common.decorators import TimeThis


class ZooKeeperDataHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def put(self, path):
        """
        Set data on a Zookeeper path
        :type path: str
        """
        logging.info('Client {0} changing data for path: {1}'
                     .format(self.request.remote_ip, path))
        if self.zk.exists(path):
            self.zk.set(path, value=self.request.body)
            data, stat = self.zk.get(path)
            self.write(data)
        else:
            self.write('Path does not exist: {0}'.format(path))
        logging.info(path)

    @TimeThis(__file__)
    def get(self, path):
        """
        Get data on a Zookeeper path
        :type path: str
        """
        logging.info('Getting data for path: {0}'.format(path))
        if self.zk.exists(path):
            data, stat = self.zk.get(path)
            self.write(data)
        else:
            self.write('Path does not exist: {0}'.format(path))
