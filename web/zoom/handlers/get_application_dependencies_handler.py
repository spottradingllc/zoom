import httplib
import json
import logging
import os
import xml.etree.ElementTree as ET

import tornado.web

class GetApplicationDependenciesHandler(tornado.web.RequestHandler):
    @property
    def zk(self):
        return self.application.zk.client

    def get(self):
        # get dependencies
        # parse configuration path from get request
        configurationPath = self.get_argument("configurationPath")

        # get agent name from configuration path
        serviceName = configurationPath[::-1]
        serviceName = serviceName[:serviceName.index("/")][::-1]

        #parse application host from configuration path
        server = self.get_argument("applicationHost")

        server = server.upper()
        path = os.path.join(self.application.configuration.agent_configuration_path, server)

        # get tuple (value, ZnodeStat) if the node exists
        if self.zk.exists(path):
            data, stat = self.zk.get(path)

            root = ET.fromstring(data)

            # get correct component within configuration
            if(root.find('Automation/Component[@id="' + serviceName + '"]') is not None):
                component = root.find('Automation/Component[@id="' + serviceName + '"]')
            else:
                component = root.find('Automation/Component[@registrationpath="' + configurationPath + '"]')

            startAction = component.find('Actions/Action[@id="start"]')

            dependencies = []
            for predicate in startAction.iter('Predicate'):
                if predicate.get('type') == 'ZookeeperHasChildren':
                    dict = {'type' : 'ZookeeperHasChildren', 'path' : predicate.get("path")}
                    dependencies.append(dict)
                if predicate.get('type') == 'ZookeeperHasGrandChildren':
                    dict = {'type' : 'ZookeeperHasGrandChildren', 'path' : predicate.get("path")}
                    dependencies.append(dict)

            self.write(json.dumps(dependencies))
        else:
            output = 'Node does not exist.'
            logging.error(output)
            self.write(output)
