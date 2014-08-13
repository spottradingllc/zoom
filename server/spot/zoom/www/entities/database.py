import logging
import pyodbc

from spot.zoom.www.entities.custom_filter import CustomFilter


class Database(object):

    def __init__(self, configuration):
        if configuration.db_type == "sql":
            self.db = SQLDatabase(configuration)

    def save_filter(self, _filter):
        return self.db.save_filter(_filter)

    def delete_filter(self, _filter):
        return self.db.delete_filter(_filter)

    def fetch_all_filters(self, login_name):
        return self.db.fetch_all_filters(login_name)

    def save_service_info(self, login_name, configuration_path, serivce_info):
        return self.db.save_service_info(login_name, configuration_path,
                                         serivce_info)

    def fetch_service_info(self, configuration_path):
        return self.db.fetch_service_info(configuration_path)


class SQLDatabase(Database):
    def __init__(self, configuration):
        self.connection_string = configuration.sql_connection
        self.connection = pyodbc.connect(self.connection_string)
        self.cursor = self.connection.cursor()

        # create the custom filters table if it doesn't exist
        if not self.cursor.tables(table="custom_filters").fetchone():
            self.cursor.execute("exec Create_Filters_Table")

        # create the services info table if it doesn't exist
        if not self.cursor.tables(table="services_info").fetchone():
            self.cursor.execute("exec Create_Info_Table")

        self.connection.commit()
        self.connection.close()

    def save_filter(self, _filter):
        connection = pyodbc.connect(self.connection_string)
        cursor = connection.cursor()

        login_name = _filter.login_name
        name = _filter.name
        parameter = _filter.parameter
        search_term = _filter.search_term
        inversed = _filter.inversed

        if inversed == "false":
            inversed = 0
        else:
            inversed = 1

        # update the filter if it exists, otherwise save
        cursor.execute("select * from custom_filters where login_name='%s' and name='%s'" % (login_name, name))
        row = cursor.fetchone()
        if row:
            cursor.execute("update custom_filters set parameter='%s', search_term='%s', inversed='%s' where login_name='%s' and name='%s'" % (parameter, search_term, inversed, login_name, name))
        else:
            cursor.execute("insert into custom_filters(login_name, name, parameter, search_term, inversed) values ('%s','%s','%s','%s',%d)" % (login_name, name, parameter, search_term, inversed))

        connection.commit()
        connection.close()
        return "Filter {0} was successfully saved in the database!".format(name)

    def delete_filter(self, _filter):
        connection = pyodbc.connect(self.connection_string)
        cursor = connection.cursor()

        login_name = _filter.login_name
        name = _filter.name

        cursor.execute("delete from custom_filters where login_name='%s' and name='%s'" % (login_name, name))
        connection.commit()
        connection.close()

        return "Filter {0} was successfully deleted from the database!".format(name)

    def fetch_all_filters(self, login_name):
        connection = pyodbc.connect(self.connection_string)
        cursor = connection.cursor()

        cursor.execute("select * from custom_filters where login_name='%s'" % login_name)
        rows = cursor.fetchall()

        filters = []
        for row in rows:
            filters.append(CustomFilter(row.name, row.login_name, row.parameter,
                                        row.search_term, row.inversed))

        connection.commit()
        connection.close()

        return filters

    def save_service_info(self, login_name, configuration_path, service_info):
        connection = pyodbc.connect(self.connection_string)
        cursor = connection.cursor()

        # update the service information if it exists, otherwise save
        cursor.execute("select * from services_info where configuration_path='%s'" % configuration_path)
        row = cursor.fetchone()
        if row:
            cursor.execute("update services_info set service_info='%s' where configuration_path='%s'" % (service_info, configuration_path))
        else:
            cursor.execute("insert into services_info(configuration_path, service_info) values ('%s','%s')" % (configuration_path, service_info))

        connection.commit()
        connection.close()
        return "Info for {} was successfully saved in the database!".format(configuration_path)

    def fetch_service_info(self, configuration_path):
        """
        :rtype: str
        """
        connection = pyodbc.connect(self.connection_string)
        cursor = connection.cursor()

        cursor.execute("select * from services_info where configuration_path='%s'" % configuration_path)
        row = cursor.fetchone()
        if row:
            return row.service_info
        else:
            logging.debug('Found no service info row for {0}'
                          .format(configuration_path))
            return ""