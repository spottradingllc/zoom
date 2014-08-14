import unittest


class NoOpTest(unittest.TestCase):
    def setUp(self):
        print "Setup"

    def tearDown(self):
        print "TearDown"

    def test_noop(self):
        print "Noop"
