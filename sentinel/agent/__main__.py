#!/usr/bin/env python

import logging
import tornado.ioloop
import platform

from source.util.helpers import setup_logging
from source.common.daemon import SentinelDaemon


if __name__ == '__main__':
    setup_logging()
    if 'Linux' in platform.platform():
        from setproctitle import setproctitle
        logging.info('Changing the process name to ZKagent')
        setproctitle('ZKagent')  # Changes process name

    with SentinelDaemon() as sentinel:
        logging.info('Starting web server loop...')
        print 'Ready to go!'
        tornado.ioloop.IOLoop.instance().start()
        logging.info('Exiting Application')