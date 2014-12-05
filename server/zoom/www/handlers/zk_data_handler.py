import logging
import tornado.ioloop
import tornado.web
import httplib

from zoom.common.decorators import TimeThis
from kazoo.exceptions import ZookeeperError


class ZooKeeperDataHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        """
        :rtype: zoom.www.zoo_keeper.ZooKeeper
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

    @TimeThis(__file__)
    def delete(self, path):
        """
        """
        if not self.zk.exists(path):
            self.write("Failed, path does not exist: {}".format(path))
            self.set_status(httplib.BAD_REQUEST)
        else:
            resp_headers = self.request.headers
            recurse = False
            user = ""
            if 'recurse' in resp_headers:
                recurse = resp_headers["recurse"]

            if 'username' in resp_headers:
                user = resp_headers["username"]
            else:
                self.write("You must provide a username")
                self.set_status(httplib.BAD_REQUEST)
                return

            if (recurse != "True" and recurse != "False"):
                self.write("Please provide recurse as either True or False")
                self.set_status(httplib.BAD_REQUEST)

            elif recurse == "True":
                try:
                    self.zk.delete(path, recursive=True)
                    logging.info(user + " recursively deleted path: " + path)
                except ZookeeperError as errno:
                    self.write("Zookeeper error occured while processing request. Error number: {}".format(errno))
                    self.set_status(httplib.INTERNAL_SERVER_ERROR)
                except Exception as e:
                    self.write("Unexpected error occured: {}".format(e))
                    self.set_status(httplib.INTERNAL_SERVER_ERROR)

            else:
                children = self.zk.get_children(path)
                if not children:
                    try:
                        self.zk.delete(path, recursive=False)
                        logging.info(user + " deleted node: " + path)
                    except ZookeeperError as errno:
                        self.write("Zookeeper error occured while processing request. Error number: {}".format(errno))
                        self.set_status(httplib.INTERNAL_SERVER_ERROR)
                    except Exception as e:
                        self.write("Unexpected error occured: {}".format(e))
                        self.set_status(httplib.INTERNAL_SERVER_ERROR)

                else:
                    self.write("Please make sure to specify with no subdirectories, or delete recursively by setting header 'recurse' to True.\n")
                    self.set_status(httplib.FORBIDDEN)
