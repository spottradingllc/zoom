import logging
import tornado.web
import tornado.httpclient
import tornado.ioloop

from kazoo.exceptions import NoNodeError


class ControlZKHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    @property
    def configuration(self):
        return self.application.configuration

    def post(self):
        # parse JSON dictionary from POST
        command = self.get_argument("command")

        logging.info("Received {0} config for Zookeeper".format(command))

        try:
            if command == "manual":
                logging.info('Updating Zookeeper global mode to {0}'
                             .format(command))
                self.zk.set(self.configuration.global_mode_path,
                            '{"mode" : "manual"}')
                self.write('Node successfully updated.')
                logging.info('Updated Zookeeper global mode to {0}'
                             .format(command))
            elif command == "auto":
                logging.info('Updating Zookeeper global mode to {0}'
                             .format(command))
                self.zk.set(self.configuration.global_mode_path,
                            '{"mode" : "auto"}')
                self.write('Node successfully updated.')
                logging.info('Updated Zookeeper global mode to {0}'
                             .format(command))
            else:
                logging.info("bad command")
        except NoNodeError:
            output = 'Could not find global mode node.'
            logging.error(output)
            self.write(output)
