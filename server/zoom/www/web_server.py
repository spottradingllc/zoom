import logging

import tornado.ioloop
import tornado.web
import tornado.websocket

from zoom.www.handlers.application_dependencies_handler import ApplicationDependenciesHandler
from zoom.www.handlers.application_opdep_handler import ApplicationOpdepHandler
from zoom.www.handlers.application_state_handler import ApplicationStateHandler
from zoom.www.handlers.application_mapping_handler import (
    ApplicationMappingHandler,
    HostMappingHandler
)
from zoom.www.handlers.control_agent_handler import ControlAgentHandler
from zoom.www.handlers.environment_handler import EnvironmentHandler
from zoom.www.handlers.delete_path_handler import DeletePathHandler
from zoom.www.handlers.filters_handler import FiltersHandler
from zoom.www.handlers.global_mode_handler import GlobalModeHandler
from zoom.www.handlers.list_servers_handler import ListServersHandler
from zoom.www.handlers.login_handler import LoginHandler
from zoom.www.handlers.pagerduty_services_handler import PagerDutyServicesHandler
from zoom.www.handlers.pagerduty_exceptions import PagerExceptionsHandler
from zoom.www.handlers.pillar_handler import PillarHandler
from zoom.www.handlers.list_pillar_servers_handler import ListPillarServersHandler
from zoom.www.handlers.salt_master_handler import SaltMasterHandler
from zoom.www.handlers.reload_cache_handler import ReloadCacheHandler
from zoom.www.handlers.sentinel_config_handler import SentinelConfigHandler
from zoom.www.handlers.service_info_handler import ServiceInfoHandler
from zoom.www.handlers.time_estimate_handler import TimeEstimateHandler
from zoom.www.handlers.zk_data_handler import ZooKeeperDataHandler
from zoom.www.handlers.zoom_ws_handler import ZoomWSHandler
from zoom.www.handlers.tools_refactor_paths import ToolsRefactorPathHandler


class WebServer(tornado.web.Application):
    def __init__(self, configuration, data_store, task_server, zk):
        """
        :type configuration: zoom.www.config.configuration.Configuration
        :type data_store: zoom.www.cache.data_store.DataStore
        :type task_server: zoom.www.entities.task_server.TaskServer
        :type zk: zoom.www.zoo_keeper.ZooKeeper
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
            (r'/api/application/states(?P<path>.*)', ApplicationStateHandler),
            (r'/api/application/dependencies(?P<path>.*)', ApplicationDependenciesHandler),
            (r'/api/application/opdep(?P<path>.*)', ApplicationOpdepHandler),
            (r'/api/application/mapping/app(?P<path>.*)', ApplicationMappingHandler),
            (r'/api/application/mapping/host/(?P<path>.*)', HostMappingHandler),
            # agent
            (r'/api/agent/', ControlAgentHandler),
            # cache
            (r'/api/cache/reload/', ReloadCacheHandler),
            # config
            (r"/api/config/list_servers/", ListServersHandler),
            (r"/api/config/(?P<server>.*)", SentinelConfigHandler),
            # delete app
            (r"/api/delete/", DeletePathHandler),
            # environment
            (r"/api/environment/", EnvironmentHandler),
            # filters
            (r"/api/filters/", FiltersHandler),
            # service info
            (r"/api/serviceinfo/", ServiceInfoHandler),
            # pagerduty
            (r"/api/pagerduty/exceptions/(?P<comp_id>.*)", PagerExceptionsHandler),
            (r"/api/pagerduty/services/", PagerDutyServicesHandler),
            # timing
            (r"/api/timingestimate", TimeEstimateHandler),
            # pillar
            (r"/api/pillar/list_servers/", ListPillarServersHandler),
            (r"/api/pillar/(?P<data>.*)", PillarHandler),
            # salt master rest api
            (r"/api/saltmaster/", SaltMasterHandler),
            # zookeeper data
            (r"/api/zookeeper(?P<path>.*)", ZooKeeperDataHandler),
            # zookeeper tools
            (r"/tools/refactor_path/", ToolsRefactorPathHandler),
            # tornado-specific
            (r'/(favicon.ico)', NoCacheStaticFileHandler, {"path": ""}),
            (r'/front-end/(.*)', NoCacheStaticFileHandler, {"path": self._configuration.client_path}),
            (r'/(.*\.html)', NoCacheStaticFileHandler, {"path": self._configuration.html_path}),
            (r'/images/(.*)', NoCacheStaticFileHandler, {"path": self._configuration.images_path}),
            (r'/(.*\.json)', NoCacheStaticFileHandler, {"path": self._configuration.html_path}),

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
        print "Web server initialized"
        tornado.ioloop.IOLoop.instance().start()  # blocks/holds main thread

    def stop(self):
        if tornado.ioloop.IOLoop.instance().initialized():
            tornado.ioloop.IOLoop.instance().stop()
            self._data_store.stop()
            logging.info("Web server stopped")

    @property
    def configuration(self):
        """
        :rtype configuration: zoom.config.configuration.Configuration
        """
        return self._configuration

    @property
    def data_store(self):
        """
        :rtype data_store: zoom.cache.data_store.DataStore
        """
        return self._data_store

    @property
    def task_server(self):
        """
        :rtype task_server: zoom.www.entities.task_server.TaskServer
        """
        return self._task_server

# subclass the StaticFileHandler to prevent caching in browsers
# http://stackoverflow.com/questions/12031007/disable-static-file-caching-in-tornado
class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header('Cache-control', 'no-store, no-cache, must-revalidate, max-age=0')

