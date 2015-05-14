import datetime
import logging
import os
import requests
import socket
import time


class GraphiteClient(object):
    VALID_ENVIRONMENTS = ['Staging', 'UAT', 'Production']
    GRAPHITE_PORT = 2003

    @classmethod
    def get_data(cls, metric, start=None, finish=None,
                 env=None, include_null=True):
        """
        Get data in JSON format from the the Graphite URL API.
        http://graphite.wikidot.com/url-api-reference

        :type metric: str
        :type start: datetime.datetime or datetime.timedelta or None
        :type finish: datetime.datetime or datetime.timedelta or None
        :type env: str
        :param include_null: Whether to include NULL values in data set
        :type include_null: bool
        :rtype: list
        """
        log = logging.getLogger('graphite')
        begin = cls._get_begin_or_end(start, '-1days')
        end = cls._get_begin_or_end(finish, 'now')

        uri = ('http://{0}/render?from={1}&until={2}&target={3}&format=json'
               .format(cls._get_host(environment=env), begin, end, metric))

        log.debug(uri)

        response = requests.get(uri)
        # filter out datapoings for the metric we're looking for
        # from [{"target": "..." , "datapoints": [...] }]
        data = [i[u'datapoints'] for i in response.json()
                if i[u'target'] == metric]
        if data:  # if data found at the metric name
            if not include_null:
                return [i for i in data[0] if i[0] is not None]
            else:
                return data[0]
        else:
            return list()

    @classmethod
    def send(cls, metric, data, tstamp=None, env=None):
        """
        Send data to Graphite.
        :type metric: str
        :type data: int or float
        :type tstamp: int or None
        :type env: str or None
        """
        log = logging.getLogger('graphite')
        if tstamp is None:
            tstamp = int(time.time())

        host = cls._get_host(environment=env)
        payload = '{0} {1} {2}'.format(metric, data, tstamp)
        log.debug('Sending message "{0}" to {1}:{2}'
                  .format(payload, host, GraphiteClient.GRAPHITE_PORT))

        sock = socket.socket()
        sock.settimeout(10)
        sock.connect((host, GraphiteClient.GRAPHITE_PORT))
        sock.sendall(payload + '\n')
        sock.close()

    @classmethod
    def _get_host(cls, environment=None):
        """
        :type environment: str
        :rtype: str
        """
        if environment is None:
            environment = os.environ.get('EnvironmentToUse', None)
            
        assert environment in GraphiteClient.VALID_ENVIRONMENTS, \
                ("Invalid 'EnvironmentToUse' variable: {0} "
                 .format(environment))

        return 'haproxy{0}'.format(environment.lower())

    @classmethod
    def _get_begin_or_end(cls, dtime, default):
        """
        :type dtime: datetime.datetime or datetime.timedelta or None
        """
        log = logging.getLogger('graphite')
        if dtime is None:
            ret_dtime = default
        elif isinstance(dtime, datetime.datetime):
            ret_dtime = cls.get_posix_time(dtime)
        elif isinstance(dtime, datetime.timedelta):
            ret_dtime = cls.get_posix_time(datetime.datetime.now() + dtime)
        else:
            log.warn('Time "{0}" is not of the proper type. Using default value'
                     ' "{1}".'.format(dtime, default))
            ret_dtime = default

        return ret_dtime

    @staticmethod
    def get_posix_time(dt):
        """
        Convert to POSIX time.
        :type dt: datetime.datetime
        :rtype: int
        """
        p = time.mktime(dt.timetuple())
        return int(p)

