import unittest
import logging
import mox
import kazoo
from nose.tools import nottest
from zoom.config.configuration import Configuration
from zoom.zoo_keeper import ZooKeeper
from zoom.cache.data_store import DataStore
from zoom.cache.global_cache import GlobalCache
from zoom.cache.application_state_cache import ApplicationStateCache
from test.test_utils import ConfigurationMock


class DataStoreTest(unittest.TestCase):
    
    def setUp(self):
        self.mox = mox.Mox()
        self.configuration = ConfigurationMock
        self.zoo_keeper = self.mox.CreateMock(ZooKeeper)

    def tearDown(self):
       self.mox.UnsetStubs()
    
    def test_construct(self):
        self.mox.ReplayAll()
        store = DataStore(self.configuration, self.zoo_keeper)
        self.mox.VerifyAll()

    def test_clients_empty(self):
        client = self.mox.CreateMockAnything()
        self.mox.ReplayAll()
        store = DataStore(self.configuration, self.zoo_keeper)
        self.assertEquals(store.web_socket_clients, [])
        store._web_socket_clients.append(client)
        self.assertEquals(store.web_socket_clients, [client])
        self.mox.VerifyAll()

    def test_global(self):
        global_cache = self.mox.CreateMock(GlobalCache)
        global_cache.get_mode()
        self.mox.ReplayAll()
        store = DataStore(self.configuration, self.zoo_keeper)
        store._global_cache=global_cache
        store.get_global_mode()
        self.mox.VerifyAll()

    def test_app_state_load(self):
        application_state_cache = self.mox.CreateMock(ApplicationStateCache)
        application_state_cache.load()
        self.mox.ReplayAll()
        store = DataStore(self.configuration, self.zoo_keeper)
        store._application_state_cache=application_state_cache
        store.load_application_state_cache()
        self.mox.VerifyAll()
        





