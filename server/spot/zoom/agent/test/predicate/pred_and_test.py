import mox
import unittest

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate
from spot.zoom.agent.sentinel.predicate.pred_and import PredicateAnd


class PredicateAndTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate And"

        self.predFalse1 = self.mox.CreateMock(SimplePredicate)
        self.predFalse1.met = False

        self.predFalse2 = self.mox.CreateMock(SimplePredicate)
        self.predFalse2.met = False

        self.predTrue1 = self.mox.CreateMock(SimplePredicate)
        self.predTrue1.met = True

        self.predTrue2 = self.mox.CreateMock(SimplePredicate)
        self.predTrue2.met = True

    def tearDown(self):
        pass

    def testmet_true_true(self):

        preds = (self.predTrue1, self.predTrue2)
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(self.comp_name, preds)
        self.assertTrue(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_true(self):

        preds = (self.predFalse1, self.predTrue2)
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(self.comp_name, preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_false(self):

        preds = (self.predFalse1, self.predFalse2)
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(self.comp_name, preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def test_start(self):

        preds = (self.predFalse1, self.predFalse2)
        self.predFalse1.start()
        self.predFalse2.start()
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(self.comp_name, preds)

        pred.start()
        pred.start()  # should noop

        self.mox.VerifyAll() 

    def test_no_stop(self):

        preds = (self.predFalse1, self.predFalse2)
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(self.comp_name, preds)

        # test stop isn't called without starting
        pred.stop()
        
        self.mox.VerifyAll() 

    def test_stop(self):

        preds = (self.predFalse1, self.predFalse2)

        self.predFalse2.start()
        self.predFalse1.start()
        self.predFalse1.stop()
        self.predFalse2.stop()
        self.predFalse1.start()
        self.predFalse2.start()
        
        self.mox.ReplayAll()
        
        pred = PredicateAnd(comp_name="tet", predicates=preds,
                            parent="Parent_str")

        pred.start()
        pred.stop()
        pred.stop()
        pred.start()

        self.mox.VerifyAll()

    def test_equal(self):

        preds1 = (self.predFalse1, self.predTrue1)
        preds2 = (self.predFalse2, self.predTrue2)
        
        self.mox.ReplayAll()
        
        pred1 = PredicateAnd(self.comp_name, preds1)
        pred2 = PredicateAnd(self.comp_name, preds2)

        self.assertTrue(pred1 == pred2)

        self.mox.VerifyAll() 

    def test_not_equal(self):
    
        pred1 = SimplePredicate(self.comp_name)
        pred1.set_met(False)
        preds1 = (pred1,)
        
        pred2 = SimplePredicate(self.comp_name)
        pred2.set_met(True)
        preds2 = (pred2,)

        self.mox.ReplayAll()
        
        pred_and1 = PredicateAnd(self.comp_name, preds1)
        pred_and2 = PredicateAnd(self.comp_name, preds2)

        self.assertNotEqual(pred_and1, pred_and2)

        self.mox.VerifyAll()