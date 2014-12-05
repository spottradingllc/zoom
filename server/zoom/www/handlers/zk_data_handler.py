import httplib
import json
import logging
import tornado.ioloop
import tornado.web

from kazoo.exceptions import (
    ZookeeperError,
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
    def put(self, path):
        """
        Set data on a Zookeeper path
        :type path: str
        """
        logging.info('Client {0} changing data for path: {1}'
                     .format(self.request.remote_ip, path))
        if self.zk.exists(path):
            self.zk.set(path, value=self.request.body)
            data, stat = self.zk.get(path)
            self.write(data)
        else:
            self.write('Path does not exist: {0}'.format(path))
        logging.info(path)

    @TimeThis(__file__)
    def get(self, path):
        """
        Get data on a Zookeeper path
        :type path: str
        """
        logging.info('Getting data for path: {0}'.format(path))
        if self.zk.exists(path):
            data, stat = self.zk.get(path)
            self.write(data)
        else:
            self.write('Path does not exist: {0}'.format(path))
            self.set_status(httplib.NO_CONTENT)

    @TimeThis(__file__)
    def post(self, path):
        """
        Create Zookeeper node
        :type path: str
        """
        try:
            user = self.get_argument('username', default=None)
            makepath = self._check_bool_str(
                self.get_argument('makepath', default='False'))
            data = self.get_argument('data', '')

            if user is None:
                self.write("You must provide a username")
                self.set_status(httplib.BAD_REQUEST)
                return

            self.zk.create(path, value=json.dumps(data), makepath=makepath)
            logging.info('Path created. User={0}, path={1}'.format(user, path))
            self.set_status(httplib.CREATED)

        except NoNodeError:
            self.write('Path base does not exist for path: {0}'.format(path))
            self.set_status(httplib.REQUESTED_RANGE_NOT_SATISFIABLE)

        except NodeExistsError:
            self.write('Path at {0} already exists.'.format(path))
            self.set_status(httplib.FORBIDDEN)

        except Exception as e:
            logging.exception('Unhandled Exception.')
            self.write('Unhandled Exception occurred: {0}'.format(e))
            self.set_status(httplib.INTERNAL_SERVER_ERROR)

    @TimeThis(__file__)
    def delete(self, path):
        """
        Uses custom header in the form:
            {'username': 'john.smith', 'recurse': 'False'}
        :type path: str
        """
        recurse = self._check_bool_str(self.request.headers.get('recurse'))
        user = self.request.headers.get('username')

        if user is None:
            self.write("You must provide a username")
            self.set_status(httplib.BAD_REQUEST)
            return

        if recurse is None:
            self.write("Please provide recurse as either True or False")
            self.set_status(httplib.BAD_REQUEST)
            return

        try:
            self.zk.delete(path, recursive=recurse)
            logging.info("User {0} initiated delete. Path={1}, "
                         "recursive={2}".format(user, path, recurse))

        except NoNodeError:
            self.write("Failed, path does not exist: {0}".format(path))
            self.set_status(httplib.NO_CONTENT)
        except NotEmptyError:
            self.write("Please make sure to specify with no subdirectories,"
                       " or delete recursively by setting header 'recurse' "
                       "to True.\n")
            self.set_status(httplib.FORBIDDEN)
        except ZookeeperError as e:
            self.write("Zookeeper error occured while processing request. "
                       "Error number: {0}".format(e))
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
        except Exception as e:
            self.write("Unexpected error occured: {0}".format(e))
            self.set_status(httplib.INTERNAL_SERVER_ERROR)

    def _check_bool_str(self, string):
        if string is None:
            return None

        if string.lower() == 'true':
            return True
        elif string.lower() == 'false':
            return False
        else:
            return None