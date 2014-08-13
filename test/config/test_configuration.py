from unittest import TestCase
from server.configuration import Configuration


class TestApplicationState(TestCase):
    def test_actual(self):
        Configuration([])

    def test_failed(self):
        caught = False
        try:
            Configuration(["configuration.py"])
        except Exception:
            caught = True
        self.assertTrue(caught)
