import mox
import unittest

from spot.zoom.agent.sentinel.predicate.simple import SimplePredicate


class PredicateSimpleTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Simple"

    def tearDown(self):
        pass

    def testmet_true(self):
        pred = SimplePredicate(self.comp_name)
        pred.set_met(True)
        self.assertTrue(pred.met)

    def testmet_false(self):
        pred = SimplePredicate(self.comp_name)
        self.assertFalse(pred.met)

    def testmet_return_to_false(self):
        pred = SimplePredicate(self.comp_name)
        pred.set_met(True)
        pred.set_met(False)
        self.assertFalse(pred.met)

    def test_equal(self):
        pred1 = SimplePredicate(self.comp_name)
        pred2 = SimplePredicate(self.comp_name)

        self.assertTrue(pred1 == pred2)

    def test_not_equal(self):
        pred1 = SimplePredicate(self.comp_name)
        pred2 = SimplePredicate(self.comp_name + "Foo")

        self.assertNotEqual(pred1, pred2)
