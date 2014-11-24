import json
import logging

from zoom.common.types import UpdateType


class ApplicationDependenciesMessage(object):
    def __init__(self):
        self._message_type = UpdateType.APPLICATION_DEPENDENCY_UPDATE
        self._operation_type = None
        self._application_dependencies = dict()

    @property
    def message_type(self):
        return self._message_type

    @property
    def application_dependencies(self):
        return self._application_dependencies

    def update(self, item):
        """
        :type item: dict
        """
        self._application_dependencies.update(item)

    def combine(self, message):
        """
        :type message: ApplicationDependenciesMessage
        """
        self._application_dependencies.update(message.application_dependencies)

    def remove(self, item):
        """
        :type item: dict
        """
        for key in item.keys():
            try:
                logging.debug('Removing from cache: {0}'.format(key))
                del self._application_dependencies[key]
            except KeyError:
                continue

    def clear(self):
        self._application_dependencies.clear()

    def to_json(self):
        return json.dumps({
            "update_type": self._message_type,
            "application_dependencies": self._application_dependencies.values()
        })

    def __len__(self):
        return len(self._application_dependencies)
