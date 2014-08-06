import unittest
import logging
import mox
from nose.tools import nottest
from sentinel.util.decorators import time_this


class NoOpTest(unittest.TestCase):
    def setUp(self):
        print "Setup"

    def tearDown(self):
        print "TearDown"

    def test_noop(self):
        print "Noop"

    

