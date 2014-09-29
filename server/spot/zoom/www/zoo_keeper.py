import logging
from kazoo.client import KazooClient
from spot.zoom.common.constants import ZK_CONN_STRING


class ZooKeeper(object):
    def __init__(self):
        self._kazoo = None

    @property
    def client(self):
        """
        :rtype: kazoo.client.KazooClient
        """
        return self._kazoo

    def start(self):
        try:
            self._kazoo = KazooClient(hosts=ZK_CONN_STRING)
            self._kazoo.start()
            logging.info("ZooKeeper client started against cluster <{0}>"
                         .format(ZK_CONN_STRING))

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
