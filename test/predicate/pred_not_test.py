import mox
import unittest

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.pred_not import PredicateNot


class PredicateNotTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Not"

    def tearDown(self):
        pass

    def testmet_true(self):

        pred = self._create_simple_pred(met=False)
        
        self.mox.ReplayAll()
        
        pred_not = self._create_pred_not(pred)
        self.assertTrue(pred_not.met)

        self.mox.VerifyAll() 

    def testmet_false(self):

        pred = self._create_simple_pred(met=True)
        
        self.mox.ReplayAll()
        
        pred_not = self._create_pred_not(pred)
        self.assertFalse(pred_not.met)

        self.mox.VerifyAll() 

    def test_start(self):

        pred = self._create_simple_pred(met=False)
        pred.start()
        
        self.mox.ReplayAll()
        
        pred_not = self._create_pred_not(pred)

        pred_not.start()
        pred_not.start()  # should noop

        self.mox.VerifyAll() 

    def test_no_stop(self):

        pred = self._create_simple_pred(met=False)
        
        self.mox.ReplayAll()
        
        pred_not = self._create_pred_not(pred)

        # test stop isn't called without starting
        pred_not.stop()
        
        self.mox.VerifyAll() 

    def test_stop(self):

        pred = self._create_simple_pred(met=False)

        pred.start()
        pred.stop()
        pred.start()
        
        self.mox.ReplayAll()
        
        pred_not = self._create_pred_not(pred)

        pred_not.start()
        pred_not.stop()
        pred_not.stop()
        pred_not.start()

        self.mox.VerifyAll()

    def test_equal(self):

        predmet1 = self._create_simple_pred(met=True)
        predmet2 = self._create_simple_pred(met=True)

        self.mox.ReplayAll()
        
        pred1 = self._create_pred_not(predmet1)
        pred2 = self._create_pred_not(predmet2)

        self.assertTrue(pred1 == pred2)

        self.mox.VerifyAll() 

    def test_not_equal(self):
    
        pred1 = self._create_simple_pred(met=False)
        pred2 = self._create_simple_pred(met=True)

        self.mox.ReplayAll()
        
        pred_and1 = self._create_pred_not(pred1)
        pred_and2 = self._create_pred_not(pred2)

        self.assertNotEqual(pred_and1, pred_and2)

        self.mox.VerifyAll()

    def _create_pred_not(self, predicate, parent='foo'):
        return PredicateNot(self.comp_name, predicate, parent=parent)

    def _create_simple_pred(self, cname=None, met=None):
        if cname is None:
            cname = self.comp_name
        s = SimplePredicate(cname, parent='foo')
        if met is not None:
            s.set_met(met)

        return s