import logging

import kazoo.client


class ZooKeeper(object):
    def __init__(self, configuration):
        """
        :type kazoo.client.KazooClient
        :type configuration: zoom.config.configuration.Configuration
        """
        self._kazoo = None
        self._configuration = configuration

    @property
    def client(self):
        """
        :rtype: kazoo.client.KazooClient
        """
        return self._kazoo

    def start(self):
        hosts = self._configuration.zookeeper_host('staging')

        try:
            self._kazoo = kazoo.client.KazooClient(hosts=hosts)
            self._kazoo.start()
            logging.info("ZooKeeper client started against cluster <{0}>".format(hosts))

        except Exception as e:
            logging.error(e)

    def stop(self):
        try:
            if self._kazoo is not None:
                self._kazoo.stop()
                self._kazoo.close()
                logging.info("ZooKeeper client stopped")
        except Exception as e:
            logging.error(e)