import unittest
import logging
import mox
from nose.tools import nottest
from sentinel.predicate.simple import SimplePredicate
from sentinel.predicate.pred_or import PredicateOr


class PredicateOrTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Or"

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
        
        pred = PredicateOr(self.comp_name, preds)
        self.assertTrue(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_true(self):

        preds = (self.predFalse1, self.predTrue2)
        
        self.mox.ReplayAll()
        
        pred = PredicateOr(self.comp_name, preds)
        self.assertTrue(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_false(self):

        preds = (self.predFalse1, self.predFalse2)
        
        self.mox.ReplayAll()
        
        pred = PredicateOr(self.comp_name, preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def test_start(self):

        preds = (self.predFalse1, self.predFalse2)
        self.predFalse1.start()
        self.predFalse2.start()
        
        self.mox.ReplayAll()
        
        pred = PredicateOr(self.comp_name, preds)

        pred.start()
        pred.start() #should noop

        self.mox.VerifyAll() 

    def test_no_stop(self):

        preds = (self.predFalse1, self.predFalse2)
        
        self.mox.ReplayAll()
        
        pred = PredicateOr(self.comp_name, preds)

        #test stop isn't called without starting
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
        
        pred = PredicateOr(self.comp_name, preds)

        pred.start()
        pred.stop()
        pred.stop()
        pred.start()

       # self.assertTrue(0)
        self.mox.VerifyAll() 

    def test_equal(self):

        pred1 = SimplePredicate(self.comp_name)
        pred1.set_met(True)
        preds1 = (pred1,)
        
        pred2 = SimplePredicate(self.comp_name)
        pred2.set_met(True)
        preds2 = (pred2,)

        self.mox.ReplayAll()
        
        pred_and1 = PredicateOr(self.comp_name, preds1)
        pred_and2 = PredicateOr(self.comp_name, preds2)

        self.assertEqual(pred_and1, pred_and2)

        self.mox.VerifyAll() 

    def test_not_equal(self):
    
        pred1 = SimplePredicate(self.comp_name)
        pred1.set_met(False)
        preds1 = (pred1,)
        
        pred2 = SimplePredicate(self.comp_name)
        pred2.set_met(True)
        preds2 = (pred2,)

        self.mox.ReplayAll()
        
        pred_and1 = PredicateOr(self.comp_name, preds1)
        pred_and2 = PredicateOr(self.comp_name, preds2)

        self.assertNotEqual(pred_and1, pred_and2)

        self.mox.VerifyAll() 
        

    

