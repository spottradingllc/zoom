class StatMock:
    def __init__(self):
        self.ephemeralOwner = None
        self.started = None


class EventMock:
    def __init__(self):
        self.path = None


class ConfigurationMock:
    def __init__(self):
        self.application_state_path = None
        self.global_mode_path = None
        self.agent_state_path = None
        self.environment = None
        self.throttle_interval = 1
        self.pagerduty_subdomain = "sub"
        self.pagerduty_api_token = "token"
        self.pagerduty_default_svc_key = "key"
        self.pagerduty_alert_footer = "footer"
        self.alert_path = "/path"
        self.override_node = "/override_foo"


class ApplicationStateMock:
    def __init__(self):
        self.mock_dict = None 
        self.configuration_path = "test/path"

    def to_dictionary(self):
        return self.mock_dict

class FakeMessage:
    def __init__(self, data):
        self.data = data

    def to_json(self):
        return self.data
