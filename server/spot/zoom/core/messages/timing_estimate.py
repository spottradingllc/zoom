import json
import logging
from zoom.entities.types import UpdateType


class TimeEstimateMessage(object):
    def __init__(self):
        self._message_type = UpdateType.TIMING_UPDATE
        self._contents = dict()

    @property
    def message_type(self):
        return self._message_type

    @property
    def contents(self):
        return self._contents

    def update(self, item):
        """
        :type item: dict
        """
        self._contents.update(item)

    def combine(self, message):
        """
        :type message: TimeEstimateMessage
        """
        self._contents.update(message.contents)

    def clear(self):
        self._contents.clear()

    def to_json(self):
        _dict = {}
        _dict.update({
            "update_type": self._message_type,
        })
        _dict.update(self.contents)

        return json.dumps(_dict)

