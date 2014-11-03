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
from spot.zoom.www.handlers.delete_path_handler import DeletePathHandler
from spot.zoom.www.handlers.filters_handler import FiltersHandler
from spot.zoom.www.handlers.global_mode_handler import GlobalModeHandler
from spot.zoom.www.handlers.list_servers_handler import ListServersHandler
from spot.zoom.www.handlers.login_handler import LoginHandler
from spot.zoom.www.handlers.pillar_handler import PillarHandler
from spot.zoom.www.handlers.list_pillar_servers_handler import ListPillarServersHandler
from spot.zoom.www.handlers.reload_cache_handler import ReloadCacheHandler
from spot.zoom.www.handlers.server_config_handler import ServerConfigHandler
from spot.zoom.www.handlers.service_info_handler import ServiceInfoHandler
from spot.zoom.www.handlers.time_estimate_handler import TimeEstimateHandler
from spot.zoom.www.handlers.zk_data_handler import ZooKeeperDataHandler
from spot.zoom.www.handlers.zoom_ws_handler import ZoomWSHandler


class WebServer(tornado.web.Application):
    def __init__(self, configuration, data_store, task_server, zk):
        """
        :type configuration: spot.zoom.config.configuration.Configuration
        :type data_store: spot.zoom.cache.data_store.DataStore
        :type task_server: spot.zoom.www.entities.task_server.TaskServer
        :type zk: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        self._configuration = configuration
        self._data_store = data_store
        self._task_server = task_server
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
            # delete app
            (r"/api/delete/", DeletePathHandler),
            # environment
            (r"/api/environment/", EnvironmentHandler),
            # filters
            (r"/api/filters/", FiltersHandler),
            # service info
            (r"/api/serviceinfo/", ServiceInfoHandler),
            # timing
            (r"/api/timingestimate", TimeEstimateHandler),
            # pillar
            (r"/api/pillar/list_servers/", ListPillarServersHandler),
            (r"/api/pillar/(?P<data>.*)", PillarHandler),
            # zookeeer data
            (r"/api/zookeeper(?P<path>.*)", ZooKeeperDataHandler),
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
            debug=configuration.is_debug,
            gzip=True
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
        """
        :rtype configuration: spot.zoom.config.configuration.Configuration
        """
        return self._configuration

    @property
    def data_store(self):
        """
        :rtype data_store: spot.zoom.cache.data_store.DataStore
        """
        return self._data_store

    @property
    def task_server(self):
        """
        :rtype task_server: spot.zoom.www.entities.task_server.TaskServer
        """
        return self._task_server
