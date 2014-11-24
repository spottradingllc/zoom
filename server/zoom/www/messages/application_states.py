import json
import logging

from zoom.common.types import UpdateType


class ApplicationStatesMessage(object):
    def __init__(self):
        self._message_type = UpdateType.APPLICATION_STATE_UPDATE
        self._application_states = dict()
        self._environment = None

    @property
    def message_type(self):
        return self._message_type

    @property
    def environment(self):
        return self._environment

    def set_environment(self, env):
        self._environment = env

    @property
    def application_states(self):
        return self._application_states

    def update(self, item):
        """
        :type item: dict
        """
        self._application_states.update(item)

    def combine(self, message):
        """
        :type message: ApplicationStatesMessage
        """
        self._application_states.update(message.application_states)

    def remove(self, item):
        """
        :type item: dict
        """
        for key in item.keys():
            try:
                logging.debug('Removing from cache: {0}'.format(key))
                del self._application_states[key]
            except KeyError:
                continue

    def clear(self):
        self._application_states.clear()

    def to_json(self):
        _dict = {}
        _dict.update({
            "update_type": self._message_type,
            "application_states": self._application_states.values()
        })
        if self.environment is not None:
            _dict.update({"environment": self._environment})
        return json.dumps(_dict)

    def __len__(self):
        return len(self._application_states)

    def remove_deletes(self):
        dels = []
        for key, value in self.application_states.iteritems():
            if value['delete']:
                dels.append(key)
        for key in dels:
            self.application_states.pop(key)
