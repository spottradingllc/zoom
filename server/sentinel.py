#!/usr/bin/env python

import logging
import platform

import tornado.ioloop
from zoom.agent.util.helpers import setup_logging
from zoom.agent.entities.daemon import SentinelDaemon


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