import logging
import os

import tornado.ioloop
import tornado.web
import tornado.websocket

from zoom.www.handlers.application_dependencies_handler import ApplicationDependenciesHandler
from zoom.www.handlers.application_opdep_handler import ApplicationOpdepHandler
from zoom.www.handlers.application_state_handler import ApplicationStateHandler
from zoom.www.handlers.regex_application_state_handler import RegexApplicationStateHandler
from zoom.www.handlers.application_mapping_handler import (
    ApplicationMappingHandler,
    HostMappingHandler
)
from zoom.www.handlers.control_agent_handler import ControlAgentHandler
from zoom.www.handlers.environment_handler import EnvironmentHandler
from zoom.www.handlers.delete_path_handler import DeletePathHandler
from zoom.www.handlers.disable_app_handler import DisableAppHandler
from zoom.www.handlers.filters_handler import FiltersHandler
from zoom.www.handlers.global_mode_handler import GlobalModeHandler
from zoom.www.handlers.list_servers_handler import ListServersHandler
from zoom.www.handlers.login_handler import LoginHandler
from zoom.www.handlers.pagerduty_services_handler import PagerDutyServicesHandler
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
from zoom.common.handlers import RUOKHandler


class WebServer(tornado.web.Application):
    def __init__(self, configuration, data_store, task_server, zk):
        """
        :type configuration: zoom.www.config.configuration.Configuration
        :type data_store: zoom.www.cache.data_store.DataStore
        :type task_server: zoom.www.entities.task_server.TaskServer
        :type zk: kazoo.client.KazooClient
        """
        self._configuration = configuration
        self._data_store = data_store
        self._task_server = task_server
        self.temp_dir = os.path.join(configuration.temp_directory, 'ruok')
        self.hostname = configuration.host
        self.zk = zk

        handlers = [
            (r'/ruok', RUOKHandler),
            (r'/login', LoginHandler),
            (r'/zoom/ws', ZoomWSHandler),
            (r'/api/v1/mode/', GlobalModeHandler),
            (r'/api/v1/application/states(?P<path>.*)', ApplicationStateHandler),
            (r'/api/v2/application/states(?P<path>.*)', RegexApplicationStateHandler),
            (r'/api/v1/application/dependencies(?P<path>.*)', ApplicationDependenciesHandler),
            (r'/api/v1/application/opdep(?P<path>.*)', ApplicationOpdepHandler),
            (r'/api/v1/application/mapping/app(?P<path>.*)', ApplicationMappingHandler),
            (r'/api/v1/application/mapping/host/(?P<path>.*)', HostMappingHandler),
            (r'/api/v1/agent/', ControlAgentHandler),
            (r'/api/v1/cache/reload/', ReloadCacheHandler),
            (r"/api/v1/config/list_servers/", ListServersHandler),
            (r"/api/v1/config/(?P<server>.*)", SentinelConfigHandler),
            (r"/api/v1/delete/", DeletePathHandler),
            (r"/api/v1/disable", DisableAppHandler),
            (r"/api/v1/environment/", EnvironmentHandler),
            (r"/api/v1/filters/", FiltersHandler),
            (r"/api/v1/serviceinfo/", ServiceInfoHandler),
            (r"/api/v1/pagerduty/services/", PagerDutyServicesHandler),
            (r"/api/v1/timingestimate(?P<path>.*)", TimeEstimateHandler),
            (r"/api/v1/pillar/list_servers/", ListPillarServersHandler),
            (r"/api/v1/pillar/(?P<data>.*)", PillarHandler),
            (r"/api/v1/saltmaster/", SaltMasterHandler),
            (r"/api/v1/zookeeper(?P<path>.*)", ZooKeeperDataHandler),
            (r"/tools/refactor_path/", ToolsRefactorPathHandler),

            (r'/(favicon.ico)', NoCacheStaticFileHandler, {"path": self._configuration.favicon_path}),
            (r'/front-end/(.*)', NoCacheStaticFileHandler, {"path": self._configuration.client_path}),
            (r'/doc/(.*)', NoCacheStaticFileHandler, {"path": self._configuration.doc_path}),
            (r'/(.*\.html)', NoCacheStaticFileHandler, {"path": self._configuration.html_path}),
            (r'/images/(.*)', NoCacheStaticFileHandler, {"path": self._configuration.images_path}),
            (r'/(.*\.json)', NoCacheStaticFileHandler, {"path": self._configuration.html_path}),

            (r'/', tornado.web.RedirectHandler, {"url": "/index.html"}),
            (r'/doc', tornado.web.RedirectHandler, {"url": "/doc/index.html"})
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


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
    """
    subclass the StaticFileHandler to prevent caching in browsers
    http://stackoverflow.com/questions/12031007/disable-static-file-caching-in-tornado
    """
    def set_extra_headers(self, path):
        self.set_header('Cache-control', 'no-store, no-cache, must-revalidate, max-age=0')
