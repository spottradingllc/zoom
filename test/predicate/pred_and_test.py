import mox
import unittest

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.pred_and import PredicateAnd


class PredicateAndTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate And"

    def tearDown(self):
        pass

    def testmet_true_true(self):
        preds = [
            self._create_simple_pred(met=True),
            self._create_simple_pred(met=True)
        ]

        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds)
        self.assertTrue(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_true(self):

        preds = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=True)
        ]
        
        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def testmet_false_false(self):

        preds = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=False)
        ]
        
        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds)
        self.assertFalse(pred.met)

        self.mox.VerifyAll() 

    def test_start(self):

        preds = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=False)
        ]
        # start predicates
        [p.start() for p in preds]

        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds)

        pred.start()
        pred.start()  # should noop

        self.mox.VerifyAll() 

    def test_no_stop(self):

        preds = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=False)
        ]
        
        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds)

        # test stop isn't called without starting
        pred.stop()
        
        self.mox.VerifyAll() 

    def test_stop(self):

        preds = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=False)
        ]

        [p.start() for p in preds]
        [p.stop() for p in preds]
        [p.start() for p in preds]

        self.mox.ReplayAll()
        
        pred = self._create_pred_and(preds, cname='tet', parent='parent_str')
        pred.start()
        pred.stop()
        pred.stop()
        pred.start()

        self.mox.VerifyAll()

    def test_equal(self):

        preds1 = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=True)
        ]
        preds2 = [
            self._create_simple_pred(met=False),
            self._create_simple_pred(met=True)
        ]
        
        self.mox.ReplayAll()
        
        pred1 = self._create_pred_and(preds1)
        pred2 = self._create_pred_and(preds2)

        self.assertTrue(pred1 == pred2)

        self.mox.VerifyAll() 

    def test_not_equal(self):
    
        pred1 = self._create_simple_pred(met=False)
        preds1 = (pred1,)
        
        pred2 = self._create_simple_pred(met=True)
        preds2 = (pred2,)

        self.mox.ReplayAll()
        
        pred_and1 = self._create_pred_and(preds1)
        pred_and2 = self._create_pred_and(preds2)

        self.assertNotEqual(pred_and1, pred_and2)

        self.mox.VerifyAll()

    def _create_pred_and(self, predicate_list, cname=None, parent='foo'):
        if cname is None:
            cname = self.comp_name

        return PredicateAnd(cname, predicate_list, parent=parent)

    def _create_simple_pred(self, cname=None, met=None):
        if cname is None:
            cname = self.comp_name
        s = SimplePredicate(cname, parent='foo')
        if met is not None:
            s.set_met(met)

        return s