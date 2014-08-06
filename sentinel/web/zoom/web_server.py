import logging
import os

import tornado.ioloop
import tornado.web
import tornado.websocket

from zoom.handlers.application_dependencies_handler import ApplicationDependenciesHandler
from zoom.handlers.application_state_handler import ApplicationStateHandler
from zoom.handlers.time_estimate_handler import TimeEstimateHandler
from zoom.handlers.control_agent_handler import ControlAgentHandler
from zoom.handlers.filters_handler import FiltersHandler
from zoom.handlers.global_mode_handler import GlobalModeHandler
from zoom.handlers.list_servers_handler import ListServersHandler
from zoom.handlers.login_handler import LoginHandler
from zoom.handlers.pillar_handler import PillarHandler
from zoom.handlers.reload_cache_handler import ReloadCacheHandler
from zoom.handlers.server_config_handler import ServerConfigHandler
from zoom.handlers.service_info_handler import ServiceInfoHandler
from zoom.handlers.zoom_ws_handler import ZoomWSHandler


class WebServer(tornado.web.Application):
    def __init__(self, configuration, data_store, zk):
        """
        :type configuration: zoom.config.configuration.Configuration
        :type data_store: zoom.cache.data_store.DataStore
        """
        self._configuration = configuration
        self._data_store = data_store
        self.zk = zk

        # initialize Tornado
        application_path = os.path.dirname(__file__)
        logging.debug("application_path <{0}>".format(application_path))

        front_end_path = os.path.join(application_path, "front-end")
        logging.debug("front_end_path <{0}>".format(front_end_path))

        html_path = os.path.join(front_end_path, "html")
        logging.debug("html_path <{0}>".format(html_path))

        handlers = [
            (r'/login', LoginHandler),
            (r'/zoom/ws', ZoomWSHandler),
            # global mode
            (r'/api/mode/', GlobalModeHandler),
            # application
            (r'/api/application/states/', ApplicationStateHandler),
            (r'/api/application/dependencies/', ApplicationDependenciesHandler),
            # agent
            (r'/api/agent/', ControlAgentHandler),
            # cache
            (r'/api/cache/reload/', ReloadCacheHandler),
            # config
            (r"/api/config/(?P<server>\w+)", ServerConfigHandler),
            (r"/api/config/list_servers/", ListServersHandler),
            # filters
            (r"/api/filters/", FiltersHandler),
            # service info
            (r"/api/serviceinfo/", ServiceInfoHandler),
            # timing
            (r"/api/timingestimate", TimeEstimateHandler),
            # pillar
            (r"/api/pillar/(?P<data>.*)", PillarHandler),
            # tornado-specific
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
            (r'/front-end/(.*)', tornado.web.StaticFileHandler, {"path": front_end_path}),
            (r'/(.*\.html)', tornado.web.StaticFileHandler, {"path": html_path}),
            (r'/(.*\.json)', tornado.web.StaticFileHandler, {"path": html_path}),
            (r'/', tornado.web.RedirectHandler, {"url": "/index.html"})
        ]

        settings = dict(
            # environment=os.environ['EnvironmentToUse'],
            # is equivalent to (autoreload=True, compiled_template_cache=False,
            # static_hash_cache=False, serve_traceback=True)
            debug=configuration.is_debug
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        logging.info("Web server initialized")

    def start(self):
        logging.info("Web server started on port <{0}>"
                     .format(self._configuration.port))
        self.listen(self._configuration.port)
        logging.info("Web server initialized")
        tornado.ioloop.IOLoop.instance().start()  # blocks/holds main thread

    def stop(self):
        if tornado.ioloop.IOLoop.instance().initialized():
            tornado.ioloop.IOLoop.instance().stop()
            logging.info("Web server stopped")

    @property
    def configuration(self):
        return self._configuration

    @property
    def data_store(self):
        return self._data_store