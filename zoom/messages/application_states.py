

class ApplicationStates(object):
    def __init__(self):
        self._message = dict(
                application_states=list()
        )

    def add(self, application_state):
        self._message['application_states'].append(application_state.to_dictionary())

    @property
    def message(self):
        return self._message

    def to_json(self):
        pass
