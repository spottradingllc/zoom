import mox
import unittest

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.pred_not import PredicateNot


class PredicateNotTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Not"

        self.predFalse1 = self.mox.CreateMock(SimplePredicate)
        self.predFalse1.met = False

        self.predTrue1 = self.mox.CreateMock(SimplePredicate)
        self.predTrue1.met = True

    def tearDown(self):
        pass

    def testmet_true(self):

        preds = self.predFalse1
        
        self.mox.ReplayAll()
        
        pred = PredicateNot(self.comp_name, preds)
        self.assertTrue(pred.met)

        self.mox.VerifyAll() 

    def testmet_false(self):

        preds = self.predTrue1
        
        self.mox.ReplayAll()
        
        pred = PredicateNot(self.comp_name, preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def test_start(self):

        preds = self.predFalse1
        self.predFalse1.start()
        
        self.mox.ReplayAll()
        
        pred = PredicateNot(self.comp_name, preds)

        pred.start()
        pred.start()  # should noop

        self.mox.VerifyAll() 

    def test_no_stop(self):

        preds = self.predFalse1
        
        self.mox.ReplayAll()
        
        pred = PredicateNot(self.comp_name, preds)

        # test stop isn't called without starting
        pred.stop()
        
        self.mox.VerifyAll() 

    def test_stop(self):

        preds = self.predFalse1

        self.predFalse1.start()
        self.predFalse1.stop()
        self.predFalse1.start()
        
        self.mox.ReplayAll()
        
        pred = PredicateNot(self.comp_name, preds)

        pred.start()
        pred.stop()
        pred.stop()
        pred.start()

        self.mox.VerifyAll()

    def test_equal(self):

        preds1 = self.predFalse1
        preds2 = self.predTrue1
        
        self.mox.ReplayAll()
        
        pred1 = PredicateNot(self.comp_name, preds1)
        pred2 = PredicateNot(self.comp_name, preds2)

        self.assertTrue(pred1 == pred2)

        self.mox.VerifyAll() 

    def test_not_equal(self):
    
        pred1 = SimplePredicate(self.comp_name)
        pred1.set_met(False)
        
        pred2 = SimplePredicate(self.comp_name)
        pred2.set_met(True)

        self.mox.ReplayAll()
        
        pred_and1 = PredicateNot(self.comp_name, pred1)
        pred_and2 = PredicateNot(self.comp_name, pred2)

        self.assertNotEqual(pred_and1, pred_and2)

        self.mox.VerifyAll()