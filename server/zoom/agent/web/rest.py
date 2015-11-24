import logging

import tornado.web

from zoom.agent.task.base_task_client import BaseTaskClient
from zoom.agent.web.handlers.v1 import (
    LogHandler,
    TaskHandler,
    StatusHandler
)
from zoom.common.handlers import (
    LogVerbosityHandler,
    RUOKHandler
)


class RestServer(tornado.web.Application):
    def __init__(self, children):
        """
        :type children: dict
        """
        self.log = logging.getLogger('sent.rest')
        self.children = children
        self.task_client = BaseTaskClient(children)
        handlers = [
            # Versioned
            (r"/api/v1/log/?(?P<count>\d+)?", LogHandler),
            (r"/api/v1/status/?(?P<target>[\w|\/]+)?", StatusHandler),
            (r"/api/v1/task/(?P<work>\w+)/?(?P<target>[\w|\/]+)?", TaskHandler),
            # Unversioned
            (r'/loglevel/(?P<level>\w+)', LogVerbosityHandler),
            (r"/ruok", RUOKHandler)
        ]
        tornado.web.Application.__init__(self, handlers)
        self.log.info('Created Rest Server...')
