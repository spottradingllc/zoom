import logging

import tornado.web

from spot.zoom.www.entities.database import Database
from spot.zoom.www.utils.decorators import TimeThis


class ServiceInfoHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        return self.application.configuration

    @TimeThis(__file__)
    def post(self):
        """
        Save service info
        """
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

    @TimeThis(__file__)
    def get(self):
        """
        Get service info
        """
        configuration_path = self.get_argument("configurationPath")

        db = Database(self.configuration)
        query = db.fetch_service_info(configuration_path)

        self.write({'servicedata':query})
