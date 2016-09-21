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
    RUOKHandler,
    VersionHandler
)


class RestServer(tornado.web.Application):
    def __init__(self, children, version, temp_dir, hostname, zk_object):
        """
        :type children: dict
        """
        self.log = logging.getLogger('sent.rest')
        self.children = children
        self.version = version
        self.temp_dir = temp_dir
        self.hostname = hostname
        self.zk = zk_object
        self.task_client = BaseTaskClient(children)
        handlers = [
            # Versioned
            (r"/api/v1/log/?(?P<count>\d+)?", LogHandler),
            (r"/api/v1/status/?(?P<target>[\w|\/]+)?", StatusHandler),
            (r"/api/v1/task/(?P<work>\w+)/?(?P<target>[\w|\/]+)?", TaskHandler),
            # Unversioned
            (r'/loglevel/(?P<level>\w+)', LogVerbosityHandler),
            (r"/ruok", RUOKHandler),
            (r"/version", VersionHandler)
        ]
        tornado.web.Application.__init__(self, handlers)
        self.log.info('Created Rest Server...')
