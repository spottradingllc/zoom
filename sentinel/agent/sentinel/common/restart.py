import logging


class RestartLogic(object):
    """
    Determines if service restarts are allowed or not
    """
    def __init__(self, restart_on_crash, restart_max):
        """
        :param restart_on_crash: bool or none: One-time bool set in the config
        :param restart_max: int or none
        """
        self._log = logging.getLogger('sent.restart')
        self._restart_on_crash = restart_on_crash
        self._restart_max = restart_max
        self._allowed = True
        self._count = 0

    @property
    def count(self):
        """
        Return the current number of restarts
        """
        return self._count

    @property
    def restart(self):
        """
        Return if restarts are allowed or not
        """
        self._log.debug('The restart mode is set to {0}'
                        .format(self._restart_on_crash))
        if self._restart_on_crash is False:
            return self._allowed
        else:
            return True

    @property
    def restart_max_reached(self):
        """
        Determines if number of restarts reached the max restart count
        :return: bool
        """
        result = self._count >= self._restart_max
        if result:
            self._log.error('The restart max {0} has been reached. The '
                            'process will no longer try to start.'
                            .format(self._restart_max))
        return result

    def set_false(self):
        self._log.debug('Restart allowed set to False')
        self._allowed = False

    def set_true(self):
        self._log.debug('Restart allowed set to True')
        self._allowed = True

    def reset_count(self):
        self._log.debug('Resetting start count to 0.')
        self._count = 0

    def increment_count(self):
        self._count += 1
