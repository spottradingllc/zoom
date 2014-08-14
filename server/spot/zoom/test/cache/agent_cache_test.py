import mox

from kazoo.protocol.states import WatchedEvent
from unittest import TestCase
from server.spot.zoom.www.cache.agent_cache import AgentCache
from server.spot.zoom.www.zoo_keeper import ZooKeeper


class AgentCacheTest(TestCase):
    
    def setUp(self):
        self.mox = mox.Mox()
        self.configuration = self.mox.CreateMockAnything()
        self.zoo_keeper = self.mox.CreateMock(ZooKeeper)

    def tearDown(self):
        self.mox.UnsetStubs()
    
    def test_construct(self):
        self.mox.ReplayAll()
        AgentCache(self.configuration, self.zoo_keeper)
        self.mox.VerifyAll()

    # TODO: test reload here
    # def test_clear(self):
    #     cache = AgentCache(self.configuration, self.zoo_keeper)
    #     self.mox.StubOutWithMock(cache, "load")
    #     cache.load()
    #     self.mox.ReplayAll()
    #     cache.clear()
    #     self.mox.VerifyAll()

    def test_load(self):
        self.zoo_keeper.get_children(
            mox.IgnoreArg()).AndReturn({'child1', 'child2', 'child3'})

        cache = AgentCache(self.configuration, self.zoo_keeper)

        self.mox.StubOutWithMock(cache, "_update_cache")
        cache._update_cache('child1').InAnyOrder("updates")
        cache._update_cache('child2').InAnyOrder("updates")
        cache._update_cache('child3').InAnyOrder("updates")

        self.mox.ReplayAll()
         
        cache.load()

        self.mox.VerifyAll()

    def get_data(self):
        return {
            u'1': {u'name': u'1',
                   u'state': u'ok',
                   u'platform': 0,
                   u'host': u'CHILXSTG037',
                   u'mode': u'manual',
                   u'register_path': u'regpath1'}
        }

    def test_update_cache(self):
        self.configuration.agent_state_path = "foo/"

        cache = AgentCache(self.configuration, self.zoo_keeper)
        self.mox.StubOutWithMock(cache, "get_agent_data")
        cache.get_agent_data(
            'child1',
            callback=mox.IgnoreArg()).AndReturn(self.get_data())

        callback = self.mox.CreateMockAnything()
        cache.add_callback(callback)
        callback(WatchedEvent(mox.IgnoreArg(), mox.IgnoreArg(), "regpath1"))

        self.mox.ReplayAll()

        cache._update_cache("child1")

        self.mox.VerifyAll()

    def test_data_by_path(self):
        self.configuration.agent_state_path = "foo/"

        cache = AgentCache(self.configuration, self.zoo_keeper)
        self.mox.StubOutWithMock(cache, "get_agent_data")
        cache.get_agent_data(
            'child1',
            callback=mox.IgnoreArg()).AndReturn(self.get_data())

        callback = self.mox.CreateMockAnything()
        cache.add_callback(callback)
        callback(WatchedEvent(mox.IgnoreArg(), mox.IgnoreArg(), "regpath1"))

        self.mox.ReplayAll()

        cache._update_cache("child1")
        self.assertEquals(self.get_data().get('1'),
                          cache.get_app_data_by_path('regpath1'))

        self.mox.VerifyAll()

    def test_host_by_path(self):
        self.configuration.agent_state_path = "foo/"

        cache = AgentCache(self.configuration, self.zoo_keeper)
        self.mox.StubOutWithMock(cache, "get_agent_data")
        cache.get_agent_data(
            'child1',
            callback=mox.IgnoreArg()).AndReturn(self.get_data())

        callback = self.mox.CreateMockAnything()
        cache.add_callback(callback)
        callback(WatchedEvent(mox.IgnoreArg(), mox.IgnoreArg(), "regpath1"))

        self.mox.ReplayAll()

        cache._update_cache("child1")
        self.assertEquals(self.get_data().get('1').get('host'),
                          cache.get_host_by_path('regpath1'))

        self.mox.VerifyAll()

    def test_get_agent_data(self):

        cache = AgentCache(self.configuration, self.zoo_keeper)
        self.zoo_keeper.get(
            "agent/path/agentName",
            watch=mox.IgnoreArg()).AndReturn(('{"string_data":"data"}', None))

        self.configuration.agent_state_path = "agent/path/"

        self.mox.ReplayAll()

        data = cache.get_agent_data("agentName")
        self.assertEquals(data, {"string_data": "data"})

        self.mox.VerifyAll()
