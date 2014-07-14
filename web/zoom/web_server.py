import logging
import os

import tornado.ioloop
import tornado.web
import tornado.websocket

from zoom.handlers.get_agents_handler import GetAgentsHandler
from zoom.handlers.control_agent_handler import ControlAgentHandler
from zoom.handlers.control_zk_handler import ControlZKHandler
from zoom.handlers.get_application_state_handler import GetApplicationStateHandler
from zoom.handlers.get_application_dependencies_handler import GetApplicationDependenciesHandler
from zoom.handlers.get_global_mode_handler import GetGlobalModeHandler
from zoom.handlers.login_handler import LoginHandler
from zoom.handlers.zoom_ws_handler import ZoomWSHandler

from zoom.handlers.server_config.search_server_handler import SearchServerHandler
from zoom.handlers.server_config.update_server_handler import UpdateServerHandler
from zoom.handlers.server_config.list_servers_handler import ListServersHandler
from zoom.handlers.server_config.add_server_handler import AddServerHandler
from zoom.handlers.server_config.delete_server_handler import DeleteServerHandler


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
            (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": ""}),
            (r'/login', LoginHandler),
            (r'/zoom/ws', ZoomWSHandler),
            (r'/api/get_global_mode/', GetGlobalModeHandler),
            (r'/api/get_agents/', GetAgentsHandler),
            (r'/api/get_application_states/', GetApplicationStateHandler),
            (r'/api/get_application_dependencies/', GetApplicationDependenciesHandler),
            (r'/api/control_agent/', ControlAgentHandler),
            (r'/api/control_zk/', ControlZKHandler),
            (r"/api/get_server_XML/(?P<server>\w+)", SearchServerHandler),
            (r"/api/update_server_XML/(?P<server>\w+)", UpdateServerHandler),
            (r"/api/add_server/(?P<server>\w+)", AddServerHandler),
            (r"/api/delete_server/(?P<server>\w+)", DeleteServerHandler),
            (r"/api/list_servers/", ListServersHandler),
            (r'/front-end/(.*)', tornado.web.StaticFileHandler, {"path": front_end_path}),
            (r'/(.*\.html)', tornado.web.StaticFileHandler, {"path": html_path}),
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
        logging.info("Web server started on port <{0}>".format(self._configuration.port))
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