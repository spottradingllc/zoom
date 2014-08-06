import logging
import requests
import tornado.web


class ControlAgentHandler(tornado.web.RequestHandler):
    def post(self):
        # parse JSON dictionary from POST
        configuration_path = self.get_argument("configurationPath")
        application_host = self.get_argument("applicationHost")
        command = self.get_argument("command")

        # get agent name from configuration path
        agent_name = configuration_path[::-1]
        agent_name = agent_name[:agent_name.index("/")][::-1]

        logging.info("Received {0} command for host {1} at path {2}"
                     .format(command, application_host, configuration_path))
        logging.info("Agent name, from configuration path, is {0}"
                     .format(agent_name))

        req_url = "http://{0}:9000/{1}/{2}".format(application_host,
                                                  command,
                                                  agent_name)
        logging.info("Sending POST request to {0}".format(req_url))

        response = requests.post(req_url, timeout=5.0)
        logging.info(response.json())
