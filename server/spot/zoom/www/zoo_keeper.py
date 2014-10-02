import logging
from kazoo.client import KazooClient
from spot.zoom.common.constants import ZK_CONN_STRING


class ZooKeeper(object):
    def __init__(self, zk_listener):
        self.kazoo = None
        self._zk_listener = zk_listener

    @property
    def client(self):
        """
        :rtype: kazoo.client.KazooClient
        """
        return self.kazoo

    def start(self):
        try:
            self.kazoo = KazooClient(hosts=ZK_CONN_STRING)
            self.kazoo.add_listener(self._zk_listener)
            self.kazoo.start()
            logging.info("ZooKeeper client started against cluster <{0}>"
                         .format(ZK_CONN_STRING))

        except Exception as e:
            logging.error(e)

    def stop(self):
        try:
            if self.kazoo is not None:
                self.kazoo.stop()
                self.kazoo.close()
                logging.info("ZooKeeper client stopped")
    
        except TypeError:
            pass

    def restart(self):
        self.stop()
        self.start()

    def set(self, path, value, version=-1):
        return self.kazoo.set(path, value, version=version)

    def exists(self, path, watch=None):
        return self.kazoo.exists(path=path, watch=watch)

    def get(self, path, watch=None):
        return self.kazoo.get(path=path, watch=watch)

    def delete(self, path):
        return self.kazoo.delete(path=path, recursive=True)

    def get_children(self, path, watch=None):
        return self.kazoo.get_children(path=path, watch=watch)

    def create(self, path,
               value="", ephemeral=False, sequence=False, makepath=False):
        return self.kazoo.create(path, value=value, ephemeral=ephemeral,
                                  sequence=sequence, makepath=makepath)
