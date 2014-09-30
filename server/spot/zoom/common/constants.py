import os


__env_connections = {
    "Staging": ('ZooStaging01:2181,'
                'ZooStaging02:2181,'
                'ZooStaging03:2181,'
                'ZooStaging04:2181,'
                'ZooStaging05:2181'),
#     "UAT": ('ZooUat01:2181,'
#             'ZooUat01:2181,'
#             'ZooUat01:2181,'
#             'ZooUat01:2181,'
#             'ZooUat01:2181'),
    "UAT": ('ZooProduction01:2181,'  # UAT servers will route to Production ZK
            'ZooProduction02:2181,'
            'ZooProduction03:2181,'
            'ZooProduction04:2181,'
            'ZooProduction05:2181'),
    "Production": ('ZooProduction01:2181,'
                   'ZooProduction02:2181,'
                   'ZooProduction03:2181,'
                   'ZooProduction04:2181,'
                   'ZooProduction05:2181')
}

__env = os.environ.get('EnvironmentToUse', 'Staging')
ZK_CONN_STRING = __env_connections[__env]
ZK_AGENT_CONFIG = '/spot/software/config/application/sentinel'
ZOOM_CONFIG = '/spot/software/config/application/zoom'