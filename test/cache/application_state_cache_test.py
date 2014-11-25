import mox

import unittest
from zoom.www.cache.time_estimate_cache import TimeEstimateCache
from zoom.www.cache.application_state_cache import ApplicationStateCache
from zoom.www.messages.application_states import ApplicationStatesMessage
from zoom.www.entities.zoo_keeper import ZooKeeper
from test.test_utils import (
    StatMock,
    EventMock,
    ConfigurationMock,
    ApplicationStateMock
)


class ApplicationStateCacheTest(unittest.TestCase):
    
    def setUp(self):
        self.mox = mox.Mox()
        self.socket_client1 = self.mox.CreateMockAnything()
        self.socket_client2 = self.mox.CreateMockAnything()

        self.web_socket_clients = [self.socket_client1, self.socket_client2]

        self.configuration = ConfigurationMock()
        self.configuration.environment = "Testing"
        self.configuration.agent_state_path = "/test"

        self.zoo_keeper = self.mox.CreateMock(ZooKeeper)

        self.time_estimate_cache = self.mox.CreateMock(TimeEstimateCache)

    def tearDown(self):
        self.mox.UnsetStubs()
    
    def test_construct(self):
        self.mox.ReplayAll()
        ApplicationStateCache(self.configuration, self.zoo_keeper,
                              self.web_socket_clients, self.time_estimate_cache)
        self.mox.VerifyAll()

    def test_on_update(self):
        cache = self._create_app_state_cache()

        self.mox.StubOutWithMock(cache, "_walk")
        cache._walk('path1', mox.IgnoreArg())

        event = EventMock()
        event.path = 'path1'

        self.time_estimate_cache.update_states(mox.IgnoreArg())

        self.mox.ReplayAll()
         
        cache._on_update(event)

        self.mox.VerifyAll()

    def test_get_application_state_eph0(self):

        path = "/foo/bar/head"
        test_unknown = '/test/Unknown'

        cache = self._create_app_state_cache()

        stat = StatMock()
        stat.ephemeralOwner = 0
        stat.last_modified = 0
        
        self.zoo_keeper.get(path, watch=mox.IgnoreArg()).AndReturn(("{}", stat))
        self.zoo_keeper.get_children(path, watch=mox.IgnoreArg()).AndReturn([])
        self.zoo_keeper.exists(test_unknown, watch=mox.IgnoreArg())

        self.mox.ReplayAll()
         
        cache._get_application_state(path)

        self.mox.VerifyAll()

    def test_get_application_state_eph1(self):
        foobar = "/foo/bar"
        foobarhead = "/foo/bar/head"

        cache = self._create_app_state_cache()

        stat = StatMock()
        stat.ephemeralOwner = 1
        stat.last_modified = 0
        stat.created = 1

        self.zoo_keeper.get(foobarhead, watch=mox.IgnoreArg()).InAnyOrder().AndReturn(("{}", stat))
        self.zoo_keeper.get(foobar, watch=mox.IgnoreArg()).InAnyOrder().AndReturn(("{}", stat))
        self.zoo_keeper.get_children(foobar, watch=mox.IgnoreArg()).InAnyOrder()

        self.mox.ReplayAll()
         
        cache._get_application_state(foobarhead)

        self.mox.VerifyAll()

    def fake_walk(self, path, results):
        results.update({"key": "print message"})

    def test_load(self):
        cache = self._create_app_state_cache()

        self.mox.StubOutWithMock(cache, "_load")
        cache._load()
        cache._load()

        self.mox.ReplayAll()
         
        #actually call twice
        cache.load()
        cache.load()

        cache._cache = ["0"]

        cache.load()

        self.mox.VerifyAll()

    # TODO: this should test reload
    # def test_clear(self):
    #     # need to update w/ time estimate cache
    #     cache = ApplicationStateCache(self.configuration, self.zoo_keeper,
    #                                   self.web_socket_clients )
    #     self.configuration.application_state_path = 'path1'
    #
    #     self.mox.StubOutWithMock(cache, "_on_update_path")
    #     cache._on_update_path('path1')
    #
    #     self.mox.ReplayAll()
    #
    #     cache.clear()
    #
    #     self.mox.VerifyAll()
    
    def test_walk_no_childen(self):
        cache = self._create_app_state_cache()

        self.zoo_keeper.connected = True
        self.zoo_keeper.get_children('path1', watch=mox.IgnoreArg()).AndReturn(None)

        app_state = ApplicationStateMock()
        app_state.mock_dict = {'key': 'value'}
        result = ApplicationStatesMessage()
        compare = dict()
        compare.update({ApplicationStateMock().configuration_path: app_state.to_dictionary()})

        self.mox.StubOutWithMock(cache, "_get_application_state")
        cache._get_application_state('path1').AndReturn(app_state)

        self.mox.ReplayAll()
         
        cache._walk('path1', result)
        self.assertEquals(result, compare)

        self.mox.VerifyAll()

    def test_walk_children(self):
        cache = ApplicationStateCache(self.configuration, self.zoo_keeper,
                                      self.web_socket_clients, 
                                      self.time_estimate_cache)
        app_state1 = ApplicationStateMock()
        app_state1.mock_dict = {'key': 'value'}
        app_state1.configuration_path = "path1/foo"

        app_state2 = ApplicationStateMock()
        app_state2.mock_dict = {'key': 'value'}
        app_state2.configuration_path = "path1/bar"

        result = ApplicationStatesMessage()
        compare = dict()
        compare.update({'path1/bar': app_state2.to_dictionary()})
        compare.update({'path1/foo': app_state1.to_dictionary()})

        self.zoo_keeper.connected = True
        self.zoo_keeper.get_children('path1', watch=mox.IgnoreArg()).AndReturn(['foo', 'bar'])
        self.zoo_keeper.get_children('path1/foo', watch=mox.IgnoreArg()).AndReturn([])
        self.zoo_keeper.get_children('path1/bar', watch=mox.IgnoreArg()).AndReturn([])

        self.mox.StubOutWithMock(cache, "_get_application_state")
        cache._get_application_state('path1/foo').AndReturn(app_state2)
        cache._get_application_state('path1/bar').AndReturn(app_state1)

        self.mox.ReplayAll()
         
        cache._walk('path1', result)
        self.assertEquals(result, compare)

        self.mox.VerifyAll()

    def _create_app_state_cache(self):
        return ApplicationStateCache(self.configuration, self.zoo_keeper,
                                     self.web_socket_clients,
                                     self.time_estimate_cache)