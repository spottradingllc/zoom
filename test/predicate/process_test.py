import mox
import time

from unittest import TestCase
from multiprocessing import Lock
from zoom.agent.predicate.process import PredicateProcess
from zoom.agent.client.process_client import ProcessClient


class PredicateProcessTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.interval = 0.1
        self.proc_client = self.mox.CreateMock(ProcessClient)
        self.proc_client.process_client_lock = Lock()
        self.proc_client.cancel_flag = False

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_start(self):

        pred = PredicateProcess("/path", self.proc_client, interval=self.interval)
        self.mox.StubOutWithMock(pred, "running")
        pred.running().MultipleTimes().AndReturn(True)

        self.mox.ReplayAll() 

        pred.start()
        pred.start()  # should noop
        pred.start()  # should noop
        time.sleep(0.25)  # give other thread time to check
        pred.stop()

        self.mox.VerifyAll() 

    def test_stop(self):

        pred = PredicateProcess("/path", self.proc_client, interval=self.interval)
        self.mox.StubOutWithMock(pred, "running")
        pred.running().MultipleTimes().AndReturn(True)

        self.mox.ReplayAll() 

        pred.start()
        time.sleep(0.25)  # give other thread time to check
        pred.stop()
        pred.stop()
        pred.stop()

        self.mox.VerifyAll() 
