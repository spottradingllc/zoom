import mox

from unittest import TestCase
from server.spot.zoom.www.cache.global_cache import GlobalCache
from server.spot.zoom.www.entities.types import UpdateType
from server.spot.zoom.www.zoo_keeper import ZooKeeper
from server.spot.zoom.test.test_utils import ConfigurationMock, EventMock


class GlobalCacheTest(TestCase):
    
    def setUp(self):
        self.mox = mox.Mox()
        self.socket_client1 = self.mox.CreateMockAnything()
        self.socket_client2 = self.mox.CreateMockAnything()

        self.web_socket_clients = [self.socket_client1, self.socket_client2]
        self.configuration = ConfigurationMock
        self.zoo_keeper = self.mox.CreateMock(ZooKeeper)

    def tearDown(self):
        self.mox.UnsetStubs()
    
    def test_construct(self):
        self.mox.ReplayAll()
        GlobalCache(self.configuration, self.zoo_keeper,
                    self.web_socket_clients)
        self.mox.VerifyAll()

    def test_get_mode(self):
        self.configuration.global_mode_path = "mode/path"
        cache = GlobalCache(self.configuration, self.zoo_keeper,
                            self.web_socket_clients)
        self.zoo_keeper.get("mode/path",
                            watch=mox.IgnoreArg()).AndReturn((None, None))
        self.mox.ReplayAll()
        cache.get_mode()
        self.mox.VerifyAll()

    def test_on_update(self):
        event = EventMock()
        cache = GlobalCache(self.configuration, self.zoo_keeper,
                            self.web_socket_clients)
        self.socket_client1.write_message(
            dict(type=UpdateType.GLOBAL_MODE_UPDATE, payload= "mode_data"))
        self.socket_client2.write_message(
            dict(type=UpdateType.GLOBAL_MODE_UPDATE, payload= "mode_data"))

        self.mox.StubOutWithMock(cache, "get_mode")
        cache.get_mode().AndReturn("mode_data")

        self.mox.ReplayAll()
        cache.on_update(event)
        self.mox.VerifyAll()