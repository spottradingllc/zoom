import logging

import tornado.ioloop
import tornado.web
import tornado.websocket

from spot.zoom.www.handlers.application_dependencies_handler \
    import ApplicationDependenciesHandler
from spot.zoom.www.handlers.application_state_handler \
    import ApplicationStateHandler
from spot.zoom.www.handlers.control_agent_handler import ControlAgentHandler
from spot.zoom.www.handlers.environment_handler import EnvironmentHandler
from spot.zoom.www.handlers.filters_handler import FiltersHandler
from spot.zoom.www.handlers.global_mode_handler import GlobalModeHandler
from spot.zoom.www.handlers.list_servers_handler import ListServersHandler
from spot.zoom.www.handlers.login_handler import LoginHandler
from spot.zoom.www.handlers.pillar_handler import PillarHandler
from spot.zoom.www.handlers.reload_cache_handler import ReloadCacheHandler
from spot.zoom.www.handlers.server_config_handler import ServerConfigHandler
from spot.zoom.www.handlers.service_info_handler import ServiceInfoHandler
from spot.zoom.www.handlers.time_estimate_handler import TimeEstimateHandler
from spot.zoom.www.handlers.zoom_ws_handler import ZoomWSHandler


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
            # environment
            (r"/api/environment/", EnvironmentHandler),
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
            (r'/front-end/(.*)', tornado.web.StaticFileHandler, {"path": self._configuration.client_path}),
            (r'/(.*\.html)', tornado.web.StaticFileHandler, {"path": self._configuration.html_path}),
            (r'/(.*\.json)', tornado.web.StaticFileHandler, {"path": self._configuration.html_path}),
            (r'/', tornado.web.RedirectHandler, {"url": "/index.html"})
        ]

        settings = dict(
            # is equivalent to (autoreload=True, compiled_template_cache=False,
            # static_hash_cache=False, serve_traceback=True)
            debug=configuration.is_debug
        )

        tornado.web.Application.__init__(self, handlers, **settings)
        logging.info("Web server initialized")

    def start(self):
        self._data_store.start()
        logging.info("Web server started on port <{0}>"
                     .format(self._configuration.port))
        self.listen(self._configuration.port)
        logging.info("Web server initialized")
        tornado.ioloop.IOLoop.instance().start()  # blocks/holds main thread

    def stop(self):
        if tornado.ioloop.IOLoop.instance().initialized():
            tornado.ioloop.IOLoop.instance().stop()
            self._data_store.stop()
            logging.info("Web server stopped")

    @property
    def configuration(self):
        return self._configuration

    @property
    def data_store(self):
        return self._data_store
