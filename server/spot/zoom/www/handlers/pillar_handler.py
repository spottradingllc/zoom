import json
import logging
import os.path
import re
import tornado.web
import tornado.httpclient

from httplib import INTERNAL_SERVER_ERROR
from kazoo.exceptions import NoNodeError

from spot.zoom.common.decorators import TimeThis


class PillarHandler(tornado.web.RequestHandler):

    @property
    def pillar_path(self):
        """
        :rtype: str
        """
        return self.application.configuration.pillar_path

    @property
    def zk(self):
        """
        :rtype: spot.zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self, data):
        """
        :type data: str

        GET /{minion} > All data
        GET /{minion}/{project} > Project data
        GET /{minion}/{project}/subtype > subtype
        GET /{minion}/{project}/version > version
        """
        minion, project, data_key, data_val = self._parse_uri(data)
        minion_data = self._get_minion_data(minion)
        if project is None:
            self.write(minion_data)
            return

        project_data = minion_data.get(project, {})
        if data_key is None:
            self.write(project_data)
            return

        data_val = project_data.get(data_key, {})
        self.write(data_val)

    @TimeThis(__file__)
    def post(self, data):
        """
        :type data: str

        POST /{minion} > Create new minion
        POST /{minion}/{project} > Create new project

        Not yet implemented:
            POST /{minion}/{project} {data} > Create project with data {data}
        """
        minion, project, data_key, data_val = self._parse_uri(data)
        minion_data = self._get_minion_data(minion)

        if project is not None:
            minion_data[project] = {"subtype": None, "version": None}

        self._set_minion_data(minion, minion_data)
        self.write(minion_data)

    @TimeThis(__file__)
    def put(self, data):
        """
        :type data: str

        PUT /{minion}/{project}/subtype/{subtype_value} > update subtype
        PUT /{minion}/{project}/version/{version_value} > update version

        Not yet implemented:
            PUT /{minion}/{project} {data} > update project with data {data}
        """
        minion, project, data_key, data_val = self._parse_uri(data)
        minion_data = self._get_minion_data(minion)

        try:
            if all([minion, project, data_key, data_val]):
                minion_data[project][data_key] = data_val
                self._set_minion_data(minion, minion_data)

            self.write(minion_data)
        except KeyError as ex:
            self.set_status(INTERNAL_SERVER_ERROR)
            logging.warning("KeyError: {0}".format(ex))
            self.write({"errorText": "KeyError: {0}".format(ex)})

    @TimeThis(__file__)
    def delete(self, data):
        """
        :type data: str
        DELETE /{minion} > Delete minion
        DELETE /{minion}/{project} > Delete project
        """
        minion, project, data_key, data_val = self._parse_uri(data)
        minion_data = self._get_minion_data(minion)
        logging.info("delete1")
        if all([minion, project]):
            try:
                del minion_data[project]
            except KeyError:
                pass

            logging.info("at project delete")
            self._set_minion_data(minion, minion_data)
            self.write(minion_data)

        elif all([minion]):
            logging.info("got to delete")
            self._del_minion(minion)

    def _parse_uri(self, data):
        """
        :type data: str
        :rtype: tuple
        """
        minion = project = data_key = data_val = None

        regex = ('(?P<minion>\w+.spottrading.com)'
                 '(\/(?P<project>[\w|\-|\_]+))?'
                 '(\/(?P<data_key>\w+))?'
                 '(\/(?P<data_val>[\w|\-|\_|\.]+))?')

        match = re.search(regex, data)
        if match:
            minion = match.group('minion')
            project = match.group('project')
            data_key = match.group('data_key')
            data_val = match.group('data_val')

        return minion, project, data_key, data_val
        # else return 404?

    def _del_minion(self, minion):
        """
        :type minion: str
        :rtype: dict
        """
        path = self._assemble_path(minion)
        if self.zk.exists(path):
            self.zk.delete(path)
            logging.info("Deleted minion {0}".format(minion))
        else:
            logging.info("Minion does not exist, could not delete")

    def _get_minion_data(self, minion):
        """
        :type minion: str
        :rtype: dict
        """
        data_dict = dict()
        try:
            path = self._assemble_path(minion)
            data, stat = self.zk.get(path)
            data_dict = json.loads(data)
        except NoNodeError:
            logging.info("No node for " + path)
            pass
        except ValueError:
            logging.warning('Data at path {0} is invalid JSON.'.format(path))
        finally:
            return data_dict

    def _set_minion_data(self, minion, data):
        """
        :type minion: str
        :type data: dict
        """
        path = self._assemble_path(minion)
        if not self.zk.exists(path):
            self.zk.create(path)

        self.zk.set(path, json.dumps(data))

    def _assemble_path(self, minion):
        return os.path.join(self.pillar_path, minion)
