import json
import logging
import re
import tornado.web
import tornado.httpclient

from httplib import INTERNAL_SERVER_ERROR
from kazoo.exceptions import NoNodeError

from zoom.common.decorators import TimeThis
from zoom.agent.util.helpers import zk_path_join

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
        :rtype: zoom.www.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self, data):
        """
        @api {get} /api/pillar/:minion[/:project][/:key] Get a host's pillar values
        @apiVersion 1.0.0
        @apiName GetPillarData
        @apiGroup Pillar
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
    def actionLog(self, username, action, affected, data=""):
        """
        :type username: str
        :type action: str
        :type affected: str
        :type data: str
        """

        logString = "!!PILLAR EDITOR:"
        logString += " " + username
        logString += " " + action
        logString += " for server " + affected
        if data:
            logString += ". Entire pillar: " + data
        logging.info(logString)

    @TimeThis(__file__)
    def post(self, data):
        """
        @apiIgnore To be documented
        :type data: str

        JSON-only for creating a project with arb. data
        POST /
            JSON: {minion: name, project: name, key_n: value_n...}

        POST /{minion} > Create new minion
        POST /{minion}/{project} > Create new project
        """
        try:
            minion, project, data_key, data_val = self._parse_uri(data)
            minion_data = ""
            update_phrase = ""
            username = ""

            if self.request.body:
                jsondict = json.loads(self.request.body)
                username = jsondict["username"]

            if not minion:
                minion = jsondict["minion"]
                minion_data = jsondict["data"]
                update_phrase = jsondict["update_phrase"]

            # get_minion to create a minion - should not exist
            else:
                minion_data = self._get_minion_data(minion)

        except AttributeError as ae:
            self.write({"error": "AttributeError: {0}".format(ae)});

        # _get_minion_data will set to DOES_NOT_EXIST if minion not found

        # update existing minion
        if minion_data != {"DOES_NOT_EXIST": "true"}:
            self._set_minion_data(minion, minion_data)
            self.actionLog(username, update_phrase, minion, json.dumps(minion_data))
        # create a new minion
        else:
            minion_data = {}
            self._set_minion_data(minion, minion_data)
            self.actionLog(username, "Created new server node", minion)

        self.write(minion_data)

    @TimeThis(__file__)
    def put(self, data):
        """
        @apiIgnore To be documented
        :type data: str

        PUT /{minion}/{project}/{key}/{value} > update arbitrary key-value pair

        Not implemented, but can be done with POST and JSON:
            PUT /{minion}/{project} {data} > update project with data {data}
            PUT /{minion}/{project}/data_val/{[data_key]} > update/create data_val and key???
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
        @apiIgnore To be documented
        :type data: str
        DELETE /{minion} > Delete minion
        DELETE /{minion}/{project} > Delete project
        DELETE /{minion}/{project}/{key} > Delete Key
        """
        minion, project, data_key, data_val = self._parse_uri(data)
        minion_data = self._get_minion_data(minion)
        jsondict = json.loads(self.request.body)
        username = jsondict["username"]
        del_phrase = jsondict["del_phrase"]

        if all([data_key, minion, project]):
            try:
                del minion_data[project][data_key]

            except KeyError:
                pass

            self._set_minion_data(minion, minion_data)
            self.actionLog(username, del_phrase, minion, json.dumps(minion_data))

        elif all([minion, project]):
            try:
                del minion_data[project]
            except KeyError:
                pass

            self._set_minion_data(minion, minion_data)
            self.write(minion_data)
            self.actionLog(username, del_phrase, minion, json.dumps(minion_data))

        elif all([minion]):
            self._del_minion(minion)
            self.actionLog(username, del_phrase, minion)

    def _parse_uri(self, data):
        """
        :type data: str
        :rtype: tuple
        """
        minion = project = data_key = data_val = None

        regex = ('(?P<minion>[\w|\-]+.spottrading.com)'
                 '(\/(?P<project>[\w|\-|\_]+))?'
                 '(\/(?P<data_key>[\w|\-|\_]+))?'
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
            data_dict = {'DOES_NOT_EXIST': 'true'}
            pass
        except ValueError:
            logging.warning('Data at path {0} is invalid JSON.'.format(path))
            data_dict = {'INVALID_JSON': 'true'}
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
        return zk_path_join(self.pillar_path, minion)
