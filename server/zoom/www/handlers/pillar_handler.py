import json
import logging
import re
import tornado.web
import tornado.httpclient

from kazoo.exceptions import NoNodeError

from zoom.common.decorators import TimeThis
from zoom.agent.util.helpers import zk_path_join, cap_hostname

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
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self, data):
        """
        @api {get} /api/v1/pillar/:minion[/:project][/:key] Get a host's pillar values
        @apiVersion 1.0.0
        @apiName GetPillarData
        @apiGroup Pillar
        @apiParam {string} minion The FQDN hostname
        @apiParam {string} project String describing the project
        @apiParam {string} key Arbitrary string key under the project
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
    def action_log(self, username, action, affected, data=""):
        """
        :type username: str
        :type action: str
        :type affected: str
        :type data: str
        """
        log_string = "!!PILLAR EDITOR:"
        log_string += " " + username
        log_string += " " + action
        log_string += " for server " + affected
        if data:
            log_string += ". Entire pillar: " + data
        logging.info(log_string)

    @TimeThis(__file__)
    def post(self, data):
        """
        :type data: str
        @api {post} /api/v1/pillar/[:minion][/:project] Create and update a host's pillar values
        @apiParam {String} minion The FQDN hostname
        @apiParam {string} project String describing the project
        @apiVersion 1.0.0
        @apiName SetPillarData
        @apiGroup Pillar
        @apiDescription
            Create the minion(host) if necessary, then create a
            project name under that host, if specified.
            Either can have JSON in request body where you can add
            n-number key-value fields more easily. This is the preferred
            way of editing existing ones as well. There is no
            'put' endpoint. Placing minion name and project in the URI
            is not required, they can be put into the JSON header.
        @apiHeaderExample {json} Pass params with json:
            {
              minion: CHIVLXFOO,
              project: FOO,
              key_n: value_n...
            }
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
            self.action_log(username, update_phrase, minion, json.dumps(minion_data))
        # create a new minion
        else:
            minion_data = {}
            self._set_minion_data(minion, minion_data)
            self.action_log(username, "Created new server node", minion)

        self.write(minion_data)

    @TimeThis(__file__)
    def delete(self, data):
        """
        :type data: str
        @apiVersion 1.0.0
        @apiName DeletePillarData
        @apiGroup Pillar
        @api {delete} /api/v1/pillar/:minion[/:project][/:key] Delete Minion/Project/Key
        @apiParam {string} minion The FQDN hostname
        @apiParam {string} project String describing the project
        @apiParam {string} key Arbitrary string key under the project
        @apiDescription
            Deletes the path specified.
            If only minion specified - delete an entire minion zk node,
            If minion and project specified - delete a project from the JSON
            If minion, project and key specified - delete a key from the JSON
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
            self.action_log(username, del_phrase, minion, json.dumps(minion_data))

        elif all([minion, project]):
            try:
                del minion_data[project]
            except KeyError:
                pass

            self._set_minion_data(minion, minion_data)
            self.write(minion_data)
            self.action_log(username, del_phrase, minion, json.dumps(minion_data))

        elif all([minion]):
            self._del_minion(minion)
            self.action_log(username, del_phrase, minion)

    def _parse_uri(self, data):
        """
        :type data: str
        :rtype: tuple
        """
        minion = project = data_key = data_val = None

        regex = ('(?P<minion>[\w|\-]+(\.spottrading.com)?)'
                 '(\/(?P<project>[\w|\-|\_]+))?'
                 '(\/(?P<data_key>[\w|\-|\_]+))?'
                 '(\/(?P<data_val>[\w|\-|\_|\.]+))?')

        match = re.search(regex, data)
        if match:
            _minion = match.group('minion')
            minion = cap_hostname(_minion)
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
        path = self._assemble_path(minion)
        try:
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
