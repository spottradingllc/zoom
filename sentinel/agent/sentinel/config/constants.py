import os


__env_connections = {
    "Staging" :('ZooStaging01:2181,'
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

__env = os.environ.get('EnvironmentToUse')
assert __env_connections.has_key(__env), ("Invalid 'EnvironmentToUse' variable:"
                                          "{0} ".format(__env))

ZK_CONN_STRING = __env_connections[__env]
ZK_STATE_PATH = '/spot/software/state'
ZK_CONFIG_PATH = '/spot/software/config'
ZK_TASK_PATH = '/spot/software/task'
ZK_GLOBAL_PATH = '/'.join([ZK_CONFIG_PATH, 'global'])
ZK_AGENT_STATE_PATH = '/'.join([ZK_STATE_PATH, 'agent'])
ZK_AGENT_CONFIG_PATH = '/'.join([ZK_CONFIG_PATH, 'agent'])
GRAPHITE_RUNTIME_METRIC = 'Infrastructure.startup.{0}.runtime'
GRAPHITE_RESULT_METRIC = 'Infrastructure.startup.{0}.result'
ALLOWED_WORK = [
    "start",
    "stop",
    "restart",
    "dep_restart",
    "ignore",
    "react",
    "terminate",
    "notify",
    "unregister",
    "start_if_ready"
]
CALLBACK_PRIORITY = {
    "stop": 1,
    "unregister": 2,
    "start": 3,
    "register": 4
}
