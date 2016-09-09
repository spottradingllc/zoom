import os


__env_connections = {
    "local": "localhost:2181",
    "Staging": ('zk:2181'),
    "QA": ('ZooStaging01:2181,'
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


ZK_AGENT_CONFIG = '/spot/software/config/application/sentinel'
ZOOM_CONFIG = '/spot/software/config/application/zoom'


def get_zk_conn_string(env=None):
    default = os.environ.get('EnvironmentToUse', 'Staging')
    if env and env in __env_connections:
        return __env_connections.get(env)
    else:
        return __env_connections.get(default)

# This is a dictionary of available methods in Sentinel and their
# runtime priorities. For example, we always want to run stop before start.
SENTINEL_METHODS = {
    "stop": 1,
    "unregister": 2,
    "notify": 3,
    "start": 4,
    "register": 5,
    "restart": 6,
    "dep_restart": 99,
    "ignore": 99,
    "react": 99,
    "terminate": 99,
    "start_if_ready": 99,
    "cancel": 99,
    "status": 99
}
