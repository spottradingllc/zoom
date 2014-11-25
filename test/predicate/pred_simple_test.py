import mox
import unittest

from zoom.agent.predicate.simple import SimplePredicate


class PredicateSimpleTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Simple"

    def tearDown(self):
        pass

    def testmet_true(self):
        pred = self._create_simple_pred(met=True)
        self.assertTrue(pred.met)

    def testmet_false(self):
        pred = self._create_simple_pred()
        self.assertFalse(pred.met)

    def testmet_return_to_false(self):
        pred = self._create_simple_pred()
        pred.set_met(True)
        pred.set_met(False)
        self.assertFalse(pred.met)

    def test_equal(self):
        pred1 = self._create_simple_pred()
        pred2 = self._create_simple_pred()

        self.assertTrue(pred1 == pred2)

    def test_not_equal(self):
        pred1 = self._create_simple_pred(cname=self.comp_name)
        pred2 = self._create_simple_pred(cname=self.comp_name + "Foo")

        self.assertNotEqual(pred1, pred2)

    def _create_simple_pred(self, cname=None, met=None):
        if cname is None:
            cname = self.comp_name
        s = SimplePredicate(cname, {})
        if met is not None:
            s.set_met(met)

        return s