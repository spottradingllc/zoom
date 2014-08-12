import unittest
import logging
import mox
from nose.tools import nottest
from zoom.config.configuration import Configuration


class TestApplicationState(unittest.TestCase):
    def test_actual(self):
        conf = Configuration([])
    def test_failed(self):
        caught = False
        try:
            conf = Configuration(["configuration.py"])
        except Exception:
            caught = True;
        self.assertTrue(caught)
