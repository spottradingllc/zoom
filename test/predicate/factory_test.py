import mox
import unittest

from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.factory import PredicateFactory


class PredicateFactoryTest(unittest.TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Or"
        
        self.predat = SimplePredicate("a")
        self.predat.set_met(True)
        self.predbt = SimplePredicate("b")
        self.predbt.set_met(True)

        self.predaf = SimplePredicate("a")
        self.predbf = SimplePredicate("b")

        self.list = [self.predaf, self.predbf, self.predat, self.predbt]

        self.factory = PredicateFactory(component_name="factory", parent=None,
                                        zkclient=None, proc_client=None,
                                        system=None, pred_list=self.list)

    def tearDown(self):
        pass

    def test_match(self):
        new = SimplePredicate("a")
        ret = self.factory._ensure_new(new)
        self.assertTrue(new is not ret)
        
    def test_no_match(self):
        new = SimplePredicate("c")
        ret = self.factory._ensure_new(new)
        self.assertTrue(new is ret)
