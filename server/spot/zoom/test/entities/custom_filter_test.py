from unittest import TestCase
from server.spot.zoom.www.entities.custom_filter import CustomFilter


class TestCustomFilter(TestCase):
    def setUp(self):
        self.filter = CustomFilter(name="1", login_name="2", parameter="3",
                                   search_term="4", inversed="5")

    def test_failed(self):
        self.assertEquals({'searchTerm': '4', 'inversed': '5', 'loginName': '2',
                           'parameter': '3', 'name': '1'},
                          self.filter.to_dictionary())