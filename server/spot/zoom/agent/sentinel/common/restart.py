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
        if restart_on_crash is True:
            self._restart_on_crash = True
        else:
            self._restart_on_crash = False
        self._restart_max = restart_max
        self._count = 0

    @property
    def count(self):
        """
        Return the current number of restarts
        """
        return self._count

    @property
    def restart_allowed(self):
        """
        Return if restarts are allowed or not
        :rtype: bool
        """
        return self._restart_on_crash

    @property
    def restart_max_reached(self):
        """
        Determines if number of restarts reached the max restart count
        :rtype: bool
        """
        result = self._count >= self._restart_max
        if result:
            self._log.error('The restart max {0} has been reached. The '
                            'process will no longer try to start.'
                            .format(self._restart_max))
        return result

    def reset_count(self):
        self._log.debug('Resetting start count to 0.')
        self._count = 0

    def increment_count(self):
        self._count += 1
