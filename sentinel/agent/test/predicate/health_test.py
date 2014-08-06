import unittest
import logging
import mox
import time
from nose.tools import nottest
from sentinel.predicate.health import PredicateHealth

class PredicateHealthTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.interval = 0.1

    def tearDown(self):
       self.mox.UnsetStubs()

    def test_start(self):

        pred = PredicateHealth(None, "echo", self.interval, None)
        self.mox.StubOutWithMock(pred, "_run")
        pred._run().MultipleTimes()

        self.mox.ReplayAll() 

        print "This test should complete quickly"
        pred.start()
        pred.start() #should noop
        pred.start() #should noop
        time.sleep(0.25) #give other thread time to check
        pred.stop()

        self.mox.VerifyAll() 

    def test_stop(self):

        pred = PredicateHealth(None, "echo", self.interval, None)
        self.mox.StubOutWithMock(pred, "_run")
        pred._run().MultipleTimes()

        self.mox.ReplayAll() 

        pred.start()
        time.sleep(0.25) #give other thread time to check
        pred.stop()
        pred.stop()
        pred.stop()

        self.mox.VerifyAll() 

