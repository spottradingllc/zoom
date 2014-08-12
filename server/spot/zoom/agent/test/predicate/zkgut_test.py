import unittest
import logging
import mox
from nose.tools import nottest
from sentinel.predicate.zkgut import ZookeeperGoodUntilTime

class ZookeeperGoodUntilTimeTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.interval = 0.1

    def tearDown(self):
       self.mox.UnsetStubs()

    def test_start(self):

        pred = ZookeeperGoodUntilTime(None, None, "/path", None, interval=self.interval)
        self.mox.StubOutWithMock(pred, "_watch_node")
        pred._watch_node()

        self.mox.ReplayAll() 

        print "This test should complete quickly"
        pred.start()
        pred.start() #should noop
        pred.start() #should noop
        pred.stop()

        self.mox.VerifyAll() 

    def test_stop(self):

        pred = ZookeeperGoodUntilTime(None, None, "/path", None, interval=self.interval)
        self.mox.StubOutWithMock(pred, "_watch_node")
        pred._watch_node()

        self.mox.ReplayAll() 

        pred.start()
        pred.stop()
        pred.stop()
        pred.stop()

        self.mox.VerifyAll() 

