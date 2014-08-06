import logging
import os
from argparse import ArgumentParser
from logging.handlers import TimedRotatingFileHandler
from xml.etree import ElementTree


def setup_logging():
    if not os.path.exists('logs'):
        os.mkdir('logs')

    handler = TimedRotatingFileHandler('logs/sentinel.log', when='midnight')
    handler.suffix = "%Y-%m-%d"

    fmt = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
    handler.setFormatter(fmt)

    logger = logging.getLogger('')
    ap = ArgumentParser()
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()
    if args.verbose:
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
        else:
            return cast(a)
