import logging
import json
import os.path

from kazoo.exceptions import NoNodeError

from spot.zoom.common.types import AlertActionType


class AlertManager(object):
    def __init__(self, alert_path, zk, pd):
        """
        :type alert_path: str
        :type zk: spot.zoom.www.zoo_keeper.ZooKeeper
        :type pd: from spot.zoom.common.pagerduty.PagerDuty
        """
        self._path = alert_path
        self._zk = zk
        self._pd = pd

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
        alerts = self._zk.get_children(self._path, watch=self._handle_alerts)
        for alert in alerts:
            path = os.path.join(self._path, alert)
            try:
                data, stat = self._zk.get(path)
                alert_data = json.loads(data)

                action = alert_data.get('action')
                if action == AlertActionType.TRIGGER:
                    self._pd.trigger(alert_data.get('service_key'),
                                     alert_data.get('incident_key'),
                                     alert_data.get('description'),
                                     alert_data.get('details'))
                elif action == AlertActionType.RESOLVE:
                    self._pd.resolve(alert_data.get('api_key'),
                                     alert_data.get('incident_key'))
                else:
                    logging.warning('Unknown action type: {0}'.format(action))
                    continue

                self._zk.delete(path)

            except NoNodeError:
                logging.info('No node at {0}. Skipping alert.'.format(path))
                continue
            except ValueError:
                logging.warning('Node at {0} has invalid JSON.'.format(path))
                continue
