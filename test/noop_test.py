from unittest import TestCase


class NoOpTest(TestCase):
    def setUp(self):
        print "Setup"

    def tearDown(self):
        print "TearDown"

    def test_noop(self):
        print "Noop"
