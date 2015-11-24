import logging
import tornado.web

from httplib import INTERNAL_SERVER_ERROR

from zoom.www.entities.database import Database
from zoom.common.decorators import TimeThis


class ServiceInfoHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        """
        :rtype: zoom.www.config.configuration.Configuration
        """
        return self.application.configuration

    @TimeThis(__file__)
    def post(self):
        """
        Save service info
        @api {post} /api/v1/serviceinfo/ Set server notes
        @apiParam {String} loginName The user that submitted the task
        @apiParam {String} configurationPath A Zookeeper path corresponding with an Application
        @apiParam {String} serviceInfo The notes about an application
        @apiVersion 1.0.0
        @apiName SetNotes
        @apiGroup Server Notes
        """
        try:
            login_name = self.get_argument("loginName")
            configuration_path = self.get_argument("configurationPath")
            service_info = self.get_argument("serviceInfo")

            db = Database(self.configuration)
            query = db.save_service_info(login_name, configuration_path,
                                         service_info)

            if query:
                logging.info("User {0} saved service information for {1}"
                             .format(login_name, configuration_path))
                self.write(query)
            else:
                logging.info("Error occurred while saving service info for {0} by "
                             "user {1}".format(login_name, configuration_path))
                self.write("Error: Info for {0} could not be saved!"
                           .format(configuration_path))

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

    @TimeThis(__file__)
    def get(self):
        """
        Get service info
        @api {get} /api/v1/serviceinfo/ Get server Notes
        @apiParam {String} login_user The user that submitted the task
        @apiVersion 1.0.0
        @apiName GetNotes
        @apiGroup Server Notes
        """
        try:
            configuration_path = self.get_argument("configurationPath")

            db = Database(self.configuration)
            query = db.fetch_service_info(configuration_path)

            self.write({'servicedata':query})

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)
