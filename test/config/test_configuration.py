import mox
from unittest import TestCase

from kazoo.client import KazooClient
from zoom.www.config.configuration import Configuration
from zoom.common.constants import ZOOM_CONFIG


class TestConfiguration(TestCase):

    def setUp(self):
        self.mox = mox.Mox()
        self.zoom_config = (
            '{"web_server": { }, "active_directory": {}, "staging": {}, '
            '"production": {}, "zookeeper": {}, "pagerduty": {}, "database": '
            '{}, "message_throttle": {}, "logging": {"version": 1}}')

        self.zoo_keeper = self.mox.CreateMock(KazooClient)
        self.zoo_keeper.get(ZOOM_CONFIG).AndReturn((self.zoom_config, None))

        self.comp_name = "Test Predicate Or"

    def test_actual(self):
        self.mox.ReplayAll()
        # TODO: Need to mock out kazoo client here
        Configuration(self.zoo_keeper)
        self.mox.VerifyAll()

    def test_failed(self):
        caught = False
        try:
            Configuration()
        except Exception:
            caught = True
        self.assertTrue(caught)
