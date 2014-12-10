import logging


class RestartLogic(object):
    """
    Determines if service restarts are allowed or not
    """
    def __init__(self, restart_max):
        """
        :param restart_max: int or none
        """
        self._log = logging.getLogger('sent.restart')
        self._restart_max = restart_max
        self._agent_restarted = True
        self.stay_down = False
        self.ran_stop = False
        self.crashed = False
        self.count = 0

    @property
    def restart_max_reached(self):
        """
        Determines if number of restarts reached the max restart count
        :rtype: bool
        """
        result = self.count >= self._restart_max
        if result:
            self._log.error('The restart max {0} has been reached. The '
                            'process will no longer try to start.'
                            .format(self._restart_max))
        return result

    def set_stay_down(self, val):
        self._log.info('Setting stay_down to {0}.'.format(val))
        self.stay_down = bool(val)
        self._agent_restarted = False

    def set_ran_stop(self, val):
        self._log.info('Setting ran_stop to {0}.'.format(val))
        self.ran_stop = bool(val)
        self._agent_restarted = False

    def reset_count(self):
        self._log.debug('Resetting start count to 0.')
        self.count = 0

    def increment_count(self):
        self.count += 1

    def check_for_crash(self, running):
        """
        :type running: bool
        """
        self._log.debug(
            'running={0}, crashed={1}, ran_stop={2}, staydown={3}, agent={4}'
            .format(running, self.crashed, self.ran_stop, self.stay_down,
                    self._agent_restarted))

        # if it's running, we don't care that the agent just restarted
        if running:
            self._agent_restarted = False
            self.crashed = False
            return

        if not running \
                and not self.ran_stop \
                and not self.stay_down \
                and not self._agent_restarted:

            if not self.crashed:  # only log on change
                self._log.warning('Crash detected!')

            self.crashed = True

        else:
            self.crashed = False
