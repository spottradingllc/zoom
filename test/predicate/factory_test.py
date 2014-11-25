import mox
from unittest import TestCase
from zoom.agent.predicate.simple import SimplePredicate
from zoom.agent.predicate.factory import PredicateFactory
from zoom.agent.entities.thread_safe_object import ThreadSafeObject


class PredicateFactoryTest(TestCase):
    def setUp(self):
        self.mox = mox.Mox()
        self.comp_name = "Test Predicate Or"
        
        self.predat = SimplePredicate("a", ThreadSafeObject({}))
        self.predat.set_met(True)
        self.predbt = SimplePredicate("b", ThreadSafeObject({}))
        self.predbt.set_met(True)

        self.predaf = SimplePredicate("a", ThreadSafeObject({}))
        self.predbf = SimplePredicate("b", ThreadSafeObject({}))

        self.list = [self.predaf, self.predbf, self.predat, self.predbt]

        self.factory = PredicateFactory(component_name="factory", parent=None,
                                        zkclient=None, proc_client=None,
                                        system=None, pred_list=self.list,
                                        settings={})

    def tearDown(self):
        pass

    def test_match(self):
        new = SimplePredicate("a", ThreadSafeObject({}))
        ret = self.factory._ensure_new(new)
        self.assertTrue(new is not ret)
        
    def test_no_match(self):
        new = SimplePredicate("c", ThreadSafeObject({}))
        ret = self.factory._ensure_new(new)
        self.assertTrue(new is ret)
