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


class ApplicationStateMock:
    def __init__(self):
        self.mock_dict = None

    def to_dictionary(self):
        return self.mock_dict