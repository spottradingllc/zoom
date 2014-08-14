import json

from spot.zoom.www.entities.types import UpdateType


class GlobalModeMessage(object):
    def __init__(self, mode):
        self._message_type = UpdateType.GLOBAL_MODE_UPDATE
        self._operation_type = None
        self._mode = mode

    @property
    def message_type(self):
        return self._message_type

    @property
    def operation_type(self):
        return self._operation_type

    @property
    def mode(self):
        return self._mode

    def to_json(self):
        return json.dumps({
            "update_type": self._message_type,
            "operation_type": self._operation_type,
            "global_mode": self._mode
        })
