import logging
import os
from argparse import ArgumentParser
from logging.handlers import TimedRotatingFileHandler
from xml.etree import ElementTree


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


def verify_attribute(xmlpart, attribute, none_allowed=False, cast=str):
    """
    :type xmlpart: xml.etree.ElementTree.Element
    :type attribute: str
    :type none_allowed: bool
    :type cast: types.ClassType
    """
    a = xmlpart.get(attribute)
    if a is None and none_allowed is False:
        raise ValueError('XML part is missing attribute "{0}".\n{1}'
                         .format(attribute, ElementTree.tostring(xmlpart)))
    else:
        if a is None:
            return None
        elif a.upper() == 'TRUE':
            return True
        elif a.upper() == 'FALSE':
            return False
        else:
            return cast(a)
