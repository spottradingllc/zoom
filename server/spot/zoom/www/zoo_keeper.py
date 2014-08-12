import logging

import kazoo.client


class ZooKeeper(object):
    def __init__(self, configuration):
        """
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
        hosts = self._configuration.zookeeper_host

        try:
            self._kazoo = kazoo.client.KazooClient(hosts=hosts)
            self._kazoo.start()
            logging.info("ZooKeeper client started against cluster <{0}>"
                         .format(hosts))

        except Exception as e:
            logging.error(e)

    def stop(self):
        try:
            if self._kazoo is not None:
                self._kazoo.stop()
                self._kazoo.close()
                logging.info("ZooKeeper client stopped")
    
        except TypeError:
            pass

    def restart(self):
        self.stop()
        self.start()

    def set(self, path, value, version=-1):
        return self._kazoo.set(path, value, version=version)

    def exists(self, path, watch=None):
        return self._kazoo.exists(path=path, watch=watch)

    def get(self, path, watch=None):
        return self._kazoo.get(path=path, watch=watch)

    def delete(self, path):
        return self._kazoo.delete(path=path, recursive=True)

    def get_children(self, path, watch=None):
        return self._kazoo.get_children(path=path, watch=watch)

    def create(self, path,
               value="", ephemeral=False, sequence=False, makepath=False):
        return self._kazoo.create(path, value=value, ephemeral=ephemeral,
                                  sequence=sequence, makepath=makepath)
