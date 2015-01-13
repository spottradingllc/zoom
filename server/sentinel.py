#!/usr/bin/env python

import logging
import platform

import tornado.ioloop
from zoom.agent.util.helpers import setup_logging, parse_args
from zoom.agent.entities.daemon import SentinelDaemon


if __name__ == '__main__':
    args = parse_args()
    setup_logging(verbose=args.verbose)
    if 'Linux' in platform.platform():
        from setproctitle import setproctitle
        logging.info('Changing the process name to ZKagent')
        setproctitle('ZKagent')  # Changes process name

    with SentinelDaemon(args.port) as sentinel:
        logging.info('Starting web server loop...')
        print 'Ready to go!'
        tornado.ioloop.IOLoop.instance().start()
        logging.info('Exiting Application')