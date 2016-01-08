import logging
from kazoo.client import KazooClient
from zoom.common.constants import get_zk_conn_string


class ZooKeeper(object):
    def __init__(self, zk_listener, env=None):
        """
        :type zk_listener: types.FunctionType
        """
        self.kazoo = None
        self._env = env
        self._zk_listener = zk_listener

    @property
    def client(self):
        """
        :rtype: kazoo.client.KazooClient
        """
        return self.kazoo

    @property
    def connected(self):
        return self.client.connected

    def start(self):
        """
        Start KazooClient and add connection listener.
        """
        try:
            self.kazoo = KazooClient(hosts=get_zk_conn_string(env=self._env),
                                     timeout=60.0)
            self.kazoo.add_listener(self._zk_listener)
            self.kazoo.start()
            logging.info("ZooKeeper client started against cluster <{0}>"
                         .format(get_zk_conn_string(env=self._env)))

        except Exception as e:
            logging.error(e)

    def stop(self):
        """
        Stop and close KazooClient
        """
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

    def upsert(self, path, value, version=-1, watch=None,
               ephemeral=False, sequence=False, makepath=False):
        """
        Update if exists, create if doesn't

        :type path: str
        :type value: str
        :type version: int
        :type watch: types.FunctionType or None
        :type ephemeral: bool
        :type sequence: bool
        :type makepath: bool
        """
        # if exists, update
        if self.exists(path=path, watch=watch):
            self.set(path=path, value=value, version=version)
        else:
            self.create(path=path, value=value, ephemeral=ephemeral,
                        sequence=sequence, makepath=makepath)

    def get(self, path, watch=None):
        return self.kazoo.get(path=path, watch=watch)

    def delete(self, path, recursive=True):
        return self.kazoo.delete(path=path, recursive=recursive)

    def get_children(self, path, watch=None):
        print path
        return self.kazoo.get_children(path=path, watch=watch)

    def create(self, path,
               value="", ephemeral=False, sequence=False, makepath=False):
        return self.kazoo.create(path, value=value, ephemeral=ephemeral,
                                 sequence=sequence, makepath=makepath)
