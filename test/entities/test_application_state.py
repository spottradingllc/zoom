from unittest import TestCase
from spot.zoom.www.entities.application_state import ApplicationState


class TestApplicationState(TestCase):
    def setUp(self):
        self.state = ApplicationState(application_name="1",
                                      configuration_path="2",
                                      application_status="3",
                                      application_host="4",
                                      completion_time=5.0,
                                      error_state="6",
                                      local_mode="7")

    def test_repr(self):
        self.assertEquals(('ApplicationState(application_name=ApplicationState,'
                           ' configuration_path=1, application_status=2, '
                           'application_host=3, completion_time=4, error_state=5.0, '
                           'local_mode=6'
                          ),
                          repr(self.state))

    def test_to_dictionary(self):
        self.assertEquals({'application_host': '4',
                           'application_name': '1',
                           'application_status': 'unknown',
                           'configuration_path': '2',
                           'delete': False,
                           'error_state': '6',
                           'completion_time': '1969-12-31 18:00:05'}, self.state.to_dictionary())
