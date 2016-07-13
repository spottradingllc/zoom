import logging
import os
import platform

from argparse import ArgumentParser
from logging.handlers import TimedRotatingFileHandler
from xml.etree import ElementTree
from zoom.common.types import PlatformType


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('-v', '--verbose', action='store_true',
                    help='Enable verbose logging.')
    ap.add_argument('-p', '--port', type=int, default=9000,
                    help='Which port the REST server should listen on. '
                         'Default=9000')
    return ap.parse_args()


def setup_logging(verbose=False):
    """
    :type verbose: bool
    """
    if not os.path.exists('logs'):
        os.mkdir('logs')

    handler = TimedRotatingFileHandler('logs/sentinel.log', when='midnight')
    handler.suffix = "%Y-%m-%d"

    fmt = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
    handler.setFormatter(fmt)

    logger = logging.getLogger('')

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(handler)


def verify_attribute(xmlpart, attribute,
                     none_allowed=False, cast=str, default=None):
    """
    :type xmlpart: xml.etree.ElementTree.Element
    :type attribute: str
    :type none_allowed: bool
    :type cast: types.ClassType
    :type default: object
    """
    _log = logging.getLogger('util.verify_attribute')
    a = xmlpart.get(attribute)
    if a is None and none_allowed is False:
        raise ValueError('XML part is missing attribute "{0}".\n{1}'
                         .format(attribute, ElementTree.tostring(xmlpart)))
    else:
        if a is None:
            _log.debug('Returning default value: {0} for attribute: {1}'
                       .format(default, attribute))
            return default
        elif a.upper() == 'TRUE':
            return True
        elif a.upper() == 'FALSE':
            return False
        else:
            return cast(a)


def get_system():
    system_str = platform.platform(terse=True)
    if 'Linux' in system_str:
        return PlatformType.LINUX
    elif 'Windows' in system_str:
        return PlatformType.WINDOWS
    else:
        return PlatformType.UNKNOWN


def zk_path_join(*args):
    """
    Use the smart joining of os.join, but replace Windows backslashes with
    forward slashes if they are inserted due to running natively on Windows.
    :param args: iterable of strings to join
    :return: string
    """
    return os.path.join(*args).replace("\\", "/")


def get_log(count=100):
    """
    :type count: int
    :rtype: list of str
    """
    logfile = 'logs/sentinel.log'
    with open(logfile, 'r') as f:
        lines = f.readlines()
        # return last `count` rows
        return [l.rstrip('\n') for l in lines[-count:]]


def get_version():
    """
    Return the version of sentinel running
    :return: str
    """
    vfile = os.path.join(os.path.dirname(os.getcwd()), 'version.txt')
    data = ''
    try:
        with open(vfile, 'rb') as f:
            data = f.read().decode("utf-8")
    except IOError:
        # No file
        data = 'unknown'
    return data


def cap_hostname(host):
    """Helper function that translates hostnames to a consistent
    all caps name followed by lowercase .spottrading.com
    Args:
        host: a string hostname in one of the following formats:
              HOSTNAME
              hostname
              HOSTNAME.spottrading.com
              hostname.spottrading.com
    Returns:
        string as HOSTNAME.spottrading.com
    """
    # TODO: What about NODE.spottrading?
    # TODO: This makes zero sense for non-spottrading people.
    if '.spottrading.com' not in host:
        host = host + '.spottrading.com'
    _split = host.split('.')
    server = '.'.join([_split[0].upper()] + _split[1:])
    logging.debug('Converted: {0} to {1}'.format(host, server))
    return server
