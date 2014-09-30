import logging
import json
import os.path

from kazoo.exceptions import NoNodeError

from spot.zoom.common.pagerduty import PagerDuty
from spot.zoom.common.types import AlertActionType


class AlertManager(object):
    def __init__(self, path, zk):
        """
        :type path: str
        :type zk: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        self._path = path
        self._zk = zk

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

                p = PagerDuty(alert_data.get('subdomain'),
                              alert_data.get('org_token'),
                              alert_data.get('svc_token'))

                action = alert_data.get('action')

                if action == AlertActionType.TRIGGER:
                    p.trigger(alert_data.get('key'),
                              alert_data.get('description'),
                              alert_data.get('details'))
                elif action == AlertActionType.RESOLVE:
                    p.resolve(alert_data.get('key'))
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
