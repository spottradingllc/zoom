import logging
import json
import os.path

from threading import Thread
from kazoo.exceptions import NoNodeError, SessionExpiredError

from zoom.common.types import AlertActionType
from zoom.agent.util.helpers import zk_path_join

class AlertManager(object):
    def __init__(self, alert_path, zk, pd, exceptions):
        """
        :type alert_path: str
        :type zk: zoom.www.zoo_keeper.ZooKeeper
        :type pd: zoom.entities.pagerduty.PagerDuty
        :type exceptions: list
        """
        self._path = alert_path
        self._zk = zk
        self._pd = pd
        self._exceptions = exceptions
        self._threads = list()

    def start(self):
        logging.info('Starting to watch for alerts at path: {0}'
                     .format(self._path))
        self._handle_alerts()

    def stop(self):
        pass

    def _handle_alerts(self, event=None):
        """
        Watch path in ZooKeeper for node creation. If there is a node, connect
        to PagerDuty and either Trigger or Resolve an incident.
        :type event: kazoo.protocol.states.WatchedEvent or None
        """
        # TODO: sort by ctime? Could there be a race condition here?
        self._clean_up_threads()
        alerts = self._zk.get_children(self._path, watch=self._handle_alerts)
        for alert in alerts:
            path = zk_path_join(self._path, alert)
            try:
                data, stat = self._zk.get(path)
                alert_data = json.loads(data)

                action = alert_data.get('action')
                i_key = alert_data.get('incident_key')

                if action == AlertActionType.TRIGGER:
                    if not self._has_exception(i_key):
                        t = Thread(target=self._pd.trigger,
                                   name='pd_{0}'.format(i_key),
                                   args=(alert_data.get('service_key'),
                                         i_key,
                                         alert_data.get('description'),
                                         alert_data.get('details')),
                                   )
                        t.daemon = True
                        t.start()
                        self._threads.append(t)

                    else:
                        logging.info('Ignoring alert for {0}'.format(i_key))

                elif action == AlertActionType.RESOLVE:
                    t = Thread(target=self._pd.resolve,
                               name='pd_{0}'.format(i_key),
                               args=(alert_data.get('api_key'), i_key),
                               )
                    t.daemon = True
                    t.start()
                    self._threads.append(t)
                else:
                    logging.warning('Unknown action type: {0}'.format(action))
                    continue

                self._zk.delete(path)

            except NoNodeError:
                logging.info('No node at {0}. Skipping alert.'.format(path))
                continue
            except SessionExpiredError:
                logging.info('Session with ZK has expired. Will not process '
                             'alerts until reconnect.')
            except ValueError:
                logging.warning('Node at {0} has invalid JSON.'.format(path))
                continue

    def _has_exception(self, key):
        """
        :type key: str
        :rtype: bool
        """
        try:
            return zk_path_join(key.split('/')[1:-1]) in self._exceptions
        except IndexError:
            return False

    def _clean_up_threads(self):
        """
        Clean up threads that have finished.
        """

        for thread in [t for t in self._threads if not t.is_alive()]:
            try:
                self._threads.remove(thread)
                thread.join()
                del thread
            except (IndexError, ValueError):
                continue
