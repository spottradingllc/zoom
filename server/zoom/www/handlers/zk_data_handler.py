import httplib
import json
import logging
import tornado.ioloop
import tornado.web

from kazoo.exceptions import (
    NotEmptyError,
    NodeExistsError,
    NoNodeError
)
from zoom.common.decorators import TimeThis


class ZooKeeperDataHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.entities.zoo_keeper.ZooKeeper
        """
        return self.application.zk

    @TimeThis(__file__)
    def get(self, path):
        """
        @api {get} /api/zookeeper/:path Get data on a Zookeeper path
        @apiVersion 1.0.0
        @apiName GetZkData
        @apiGroup Zookeeper
        """
        ret = {"method": 'GET', "path": path, "code": httplib.OK,
               "data": None, "error": None}
        logging.debug('Getting data for path: {0}'.format(path))
        if self.zk.exists(path):
            data, stat = self.zk.get(path)

            try:
                ret['data'] = json.loads(data)
            except (ValueError, TypeError):
                ret['data'] = data

            self.write(ret)
        else:
            ret['code'] = httplib.NOT_FOUND
            ret['error'] = 'Path does not exist.'
            self.write(ret)
            self.set_status(ret['code'])

    @TimeThis(__file__)
    def put(self, path):
        """
        @api {put} /api/zookeeper/:path Set data on a Zookeeper path
        @apiVersion 1.0.0
        @apiName SetZkData
        @apiGroup Zookeeper
        """
        ret = {"method": 'PUT', "path": path, "code": httplib.OK,
               "data": None, "error": None}
        logging.debug('Client {0} changing data for path: {1}'
                      .format(self.request.remote_ip, path))
        if self.zk.exists(path):
            self.zk.set(path, value=self.request.body)
            self.write(ret)
        else:
            ret['code'] = httplib.NOT_FOUND
            ret['error'] = 'Path does not exist.'
            self.write(ret)
            self.set_status(ret['code'])

    @TimeThis(__file__)
    def head(self, path):
        """
        @api {head} /api/zookeeper/:path Return whether the path exists in Zookeeper
        @apiVersion 1.0.0
        @apiName CheckZkNode
        @apiGroup Zookeeper
        """
        ret = {"method": 'HEAD', "path": path, "code": httplib.OK,
               "data": None, "error": None}
        if self.zk.exists(path):
            self.write(ret)
        else:
            ret['code'] = httplib.NOT_FOUND
            self.write(ret)
            self.set_status(ret['code'])

    @TimeThis(__file__)
    def post(self, path):
        """
        @api {post} /api/zookeeper/:path Create Zookeeper node
        @apiParam {String} [data=''] Any string of data to set in the Zookeeper node
        @apiVersion 1.0.0
        @apiName CreateZkNode
        @apiGroup Zookeeper
        """
        ret = {"method": 'POST', "path": path, "code": httplib.OK,
               "data": None, "error": None}
        try:
            data = self.get_argument('data', '')

            self.zk.create(path, value=json.dumps(data), makepath=True)
            logging.debug('Path created. path={1}'.format(path))
            ret['code'] = httplib.CREATED
            self.write(ret)
            self.set_status(ret['code'])

        except NodeExistsError:
            ret['error'] = 'Path already exists.'
            ret['code'] = httplib.CONFLICT
            self.write(ret)
            self.set_status(ret['code'])

        except Exception as e:
            logging.exception('Unhandled Exception.')
            ret['error'] = 'Unhandled Exception occurred: {0}'.format(e)
            ret['code'] = httplib.INTERNAL_SERVER_ERROR
            self.write(ret)
            self.set_status(ret['code'])

    @TimeThis(__file__)
    def delete(self, path):
        """
        @api {delete} /api/zookeeper/:path Delete Zookeeper path
        @apiHeader {Boolean} [recurse=False]
        @apiVersion 1.0.0
        @apiName DeleteZkNode
        @apiGroup Zookeeper
        """
        ret = {"method": 'DELETE', "path": path, "code": httplib.OK,
               "data": None, "error": None}
        recurse = self._check_bool_str(self.request.headers.get('recurse', 'False'))

        if recurse is None:
            ret['error'] = "Please provide 'recurse' as a custom header. " \
                           "E.g., curl -H 'recurse: True' "
            ret['code'] = httplib.BAD_REQUEST
            self.write(ret)
            self.set_status(ret['code'])
            return

        try:
            self.zk.delete(path, recursive=recurse)
            logging.info("Delete initiated. Path={0}, recursive={1}"
                         .format(path, recurse))
            self.write(ret)

        except NoNodeError:
            ret['code'] = httplib.NOT_FOUND
            ret['error'] = 'Path does not exist.'
            self.write(ret)
            self.set_status(ret['code'])

        except NotEmptyError:
            ret['error'] = (
                "Please make sure to specify a path with no subdirectories, or "
                "delete recursively by setting 'recurse' as a custom header. "
                "E.g., curl -H 'recurse: True' ")
            ret['code'] = httplib.CONFLICT
            self.write(ret)
            self.set_status(ret['code'])

        except Exception as e:
            logging.exception('Unhandled Exception.')
            ret['error'] = 'Unhandled Exception occurred: {0}'.format(e)
            ret['code'] = httplib.INTERNAL_SERVER_ERROR
            self.write(ret)
            self.set_status(ret['code'])

    def _check_bool_str(self, string):
        if string is None:
            return None

        if string.lower() == 'true':
            return True
        elif string.lower() == 'false':
            return False
        else:
            return None