import unittest
import logging
import mox
import kazoo
from nose.tools import nottest
from zoom.cache.agent_cache import AgentCache
from zoom.cache.application_state_cache import ApplicationStateCache
from zoom.config.configuration import Configuration
from zoom.entities.types import ApplicationStatus
from zoom.entities.types import UpdateType
from zoom.zoo_keeper import ZooKeeper
from test.test_utils import StatMock
from test.test_utils import EventMock
from test.test_utils import ConfigurationMock
from test.test_utils import ApplicationStateMock 


class ApplicationStateCacheTest(unittest.TestCase):
    
    def setUp(self):
        self.mox = mox.Mox()
        self.socket_client1 = self.mox.CreateMockAnything()
        self.socket_client2 = self.mox.CreateMockAnything()

        self.web_socket_clients = [self.socket_client1, self.socket_client2]
        self.configuration = ConfigurationMock
        self.configuration.environment="Testing"
        self.zoo_keeper = self.mox.CreateMock(ZooKeeper)
        self.agent_cache = self.mox.CreateMock(AgentCache)

    def tearDown(self):
       self.mox.UnsetStubs()
    
    def test_construct(self):
        self.agent_cache.add_callback(mox.IgnoreArg())

        self.mox.ReplayAll()
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)
        self.mox.VerifyAll()

    def test_on_update(self):
        self.agent_cache.add_callback(mox.IgnoreArg())
        mox.Replay(self.agent_cache)
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)

        self.mox.StubOutWithMock(cache, "_walk")
        cache._walk('path1', mox.IgnoreArg())
        self.socket_client1.write_message(dict(type=UpdateType.APPLICATION_STATE_UPDATE, payload= dict(application_states=list())))
        self.socket_client2.write_message(dict(type=UpdateType.APPLICATION_STATE_UPDATE, payload= dict(application_states=list())))

        event = EventMock
        event.path = 'path1'

        self.mox.ReplayAll()
         
        cache._on_update(event)

        self.mox.VerifyAll()

    def test_get_application_state_eph0(self):

        path = "/foo/bar/head"

        self.agent_cache.add_callback(mox.IgnoreArg())
        self.agent_cache.get_app_data_by_path(path).AndReturn({})
        self.agent_cache.get_host_by_path(path)
        mox.Replay(self.agent_cache)

        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)

        stat = StatMock()
        stat.ephemeralOwner = 0
        
        self.zoo_keeper.get(path).AndReturn((None, stat))
        self.zoo_keeper.get_children(path, watch=mox.IgnoreArg())

        self.mox.ReplayAll()
         
        cache._get_application_state(path)

        self.mox.VerifyAll()

    def test_get_application_state_eph1(self):

        path = "/foo/bar/head"

        self.agent_cache.add_callback(mox.IgnoreArg())
        self.agent_cache.get_app_data_by_path("/foo/bar").AndReturn({})
        mox.Replay(self.agent_cache)

        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)

        stat = StatMock()
        stat.ephemeralOwner = 1
        stat.created = 1
        
        self.zoo_keeper.get(path).AndReturn((None, stat))
        self.zoo_keeper.get_children("/foo/bar", watch=mox.IgnoreArg())

        self.mox.ReplayAll()
         
        cache._get_application_state(path)

        self.mox.VerifyAll()

    def fakeWalk(self, path, results):
        results.update({"key":"print message"})

    def test_load(self):
        self.agent_cache.add_callback(mox.IgnoreArg())
        self.agent_cache.load()
        mox.Replay(self.agent_cache)
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)
        self.configuration.application_state_path = 'path1'

        self.mox.StubOutWithMock(cache, "_walk")
        cache._walk('path1', dict()).WithSideEffects(self.fakeWalk)

        self.mox.ReplayAll()
         
        #actually call twice
        cache.load()
        cache.load()

        self.mox.VerifyAll()

    def test_clear(self):
        self.agent_cache.add_callback(mox.IgnoreArg())
        mox.Replay(self.agent_cache)
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)
        self.configuration.application_state_path = 'path1'

        self.mox.StubOutWithMock(cache, "_on_update_path")
        cache._on_update_path('path1')

        self.mox.ReplayAll()
         
        cache.clear()

        self.mox.VerifyAll()
    
    def test_walk_no_childen(self):
        self.agent_cache.add_callback(mox.IgnoreArg())
        mox.Replay(self.agent_cache)
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)
        self.zoo_keeper.get_children('path1').AndReturn(None)

        app_state = ApplicationStateMock()
        app_state.mock_dict = { 'key' : 'value'}
        result = dict()
        compare = dict()
        compare.update({'path1' : app_state.to_dictionary()})

        self.mox.StubOutWithMock(cache, "_get_application_state")
        cache._get_application_state('path1').AndReturn(app_state)

        self.mox.ReplayAll()
         
        cache._walk('path1', result)
        self.assertEquals(result, compare)

        self.mox.VerifyAll()

    def test_walk_children(self):
        self.agent_cache.add_callback(mox.IgnoreArg())
        mox.Replay(self.agent_cache)
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper, self.web_socket_clients, self.agent_cache)
        app_state = ApplicationStateMock()
        app_state.mock_dict = { 'key' : 'value'}
        result = dict()
        compare = dict()
        compare.update({'path1/foo' : app_state.to_dictionary()})
        compare.update({'path1/bar' : app_state.to_dictionary()})

        self.zoo_keeper.get_children('path1').AndReturn(['foo', 'bar'])
        self.zoo_keeper.get_children('path1/foo').AndReturn(None)
        self.zoo_keeper.get_children('path1/bar').AndReturn(None)

        self.mox.StubOutWithMock(cache, "_get_application_state")
        cache._get_application_state('path1/foo').AndReturn(app_state)
        cache._get_application_state('path1/bar').AndReturn(app_state)

        self.mox.ReplayAll()
         
        cache._walk('path1', result)
        self.assertEquals(result, compare)

        self.mox.VerifyAll()


