import json
import logging
import tornado.web

from httplib import INTERNAL_SERVER_ERROR

from zoom.www.entities.database import Database
from zoom.common.decorators import TimeThis
from zoom.www.entities.custom_filter import CustomFilter
from zoom.common.types import OperationType


class FiltersHandler(tornado.web.RequestHandler):
    @property
    def configuration(self):
        """
        :rtype: zoom.www.config.configuration.Configuration
        """
        return self.application.configuration

    @TimeThis(__file__)
    def get(self):
        """
        @api {get} /api/filters Retrieve filters for user
        @apiParam {String} loginName The user that submitted the task
        @apiVersion 1.0.0
        @apiName GetFilters
        @apiGroup Filters
        """
        try:
            login_name = self.get_argument("loginName")

            db = Database(self.configuration)
            filters = db.fetch_all_filters(login_name)

            arr = []
            for f in filters:
                arr.append(f.to_dictionary())

            self.write(json.dumps(arr))
        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)

    @TimeThis(__file__)
    def post(self):
        """
        @api {post} /api/filters Save|Delete filter for user
        @apiParam {String} operation add|remove
        @apiParam {String} name The name of the filter
        @apiParam {String} loginName The user that submitted the task
        @apiParam {String} parameter The type of search filter
        @apiParam {String} searchTerm The search variable
        @apiParam {Boolean} inversed Whether to inverse the search
        @apiVersion 1.0.0
        @apiName ManageFilter
        @apiGroup Filters
        """
        try:
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

        except Exception as e:
            self.set_status(INTERNAL_SERVER_ERROR)
            self.write({'errorText': str(e)})
            logging.exception(e)