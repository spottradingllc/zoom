import logging
import tornado.web

from zoom.agent.web.handlers import LogHandler
from zoom.agent.web.handlers import WorkHandler


class RestServer(tornado.web.Application):
    def __init__(self, children, settings):
        """
        :type children: dict
        :type settings: zoom.agent.entities.thread_safe_object.ThreadSafeObject
        """
        self.log = logging.getLogger('sent.rest')
        self.children = children
        self.settings = settings
        handlers = [
            (r"/log", LogHandler),
            (r"/(?P<work>\w+)/?(?P<target>[\w|\/]+)?", WorkHandler),
        ]
        tornado.web.Application.__init__(self, handlers)
        self.log.info('Created Rest Server...')

    def get_log(self):
        """
        :rtype: list of str
        """
        logfile = 'logs/sentinel.log'
        with open(logfile, 'r') as f:
            lines = f.readlines()
            # return last 100 rows
            return [l.rstrip('\n') for l in lines[-100:]]
