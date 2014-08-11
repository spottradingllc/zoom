import logging
import tornado.web
import json

from zoom.entities.database import Database
from zoom.utils.decorators import timethis
from zoom.entities.custom_filter import CustomFilter
from zoom.entities.types import OperationType


class FiltersHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        return self.application.configuration

    @timethis(__file__)
    def get(self):
        """
        Retrieve filter
        """
        login_name = self.get_argument("loginName")

        db = Database(self.configuration)
        filters = db.fetch_all_filters(login_name)

        arr = []
        for f in filters:
            arr.append(f.to_dictionary())

        self.write(json.dumps(arr))

    @timethis(__file__)
    def post(self):
        """
        Save filter
        """
        operation = self.get_argument("operation")
        name = self.get_argument("name")
        login_name = self.get_argument("loginName")
        parameter = self.get_argument("parameter")
        search_term = self.get_argument("searchTerm")
        inversed = self.get_argument("inversed")

        f = CustomFilter(name, login_name, parameter, search_term, inversed)

        db = Database(self.configuration)

        if operation == OperationType.ADD:
            query = db.save_filter(f)
        elif operation == OperationType.REMOVE:
            query = db.delete_filter(f)
        else:
            query = None

        if query:
            logging.info("User {0} {1} filter {2}: success"
                         .format(login_name, operation, name))
            self.write(query)
        else:
            output = ("Could not {0} filter '{1}' for user {2}"
                      .format(operation, name, login_name))
            logging.warning(output)
            self.write(output)
