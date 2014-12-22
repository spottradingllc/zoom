# Zoom

Zoom is a platform created by Spot Trading to manage real-time application startup, configuration and dependency management. Zoom provides a server-side agent and front-end web interface to allow for easy administration of our software infrastructure.

## About

### The Agent

The Zoom agent is python service called Sentinel. It is responsible for watching the status of Linux daemons and Windows services. When the service is it watching is running, the agent creates a node in ZooKeeper.
 
All interaction with Sentinel happens in ZooKeeper:

- Configuration: hosted as xml text within a node in ZooKeeper. The Agent will automatically restart upon a configuration change. 
- Commands to underlying daemons: To send a 'restart' to the daemon being monitored, we created a node in ZooKeeper with JSON data inside. 


### The Web Front-end

The Web Front-end (which we simply call Zoom) is completely abstracted from the agents. This means that the agents will still run as they are configured to without the Zoom web server running. Zoom is more a means for humans to get involved should they need to start/stop an application, change the configuration of an agent, etc. 

### Technologies used

Zoom's web front-end is powered by [Tornado Web](https://github.com/tornadoweb)'s [Tornado](https://github.com/tornadoweb/tornado) web server. Our web interface was designed using Twitter's [Bootstrap](http://getbootstrap.com/) framework. In implementing Zoom's front-end, we used a handful of open-source JavaScript libraries. We simplified the inclusion and handling of these modules using [jrburke](https://github.com/jrburke)'s [RequireJS](http://requirejs.org/) library. To support real-time updates to Zoom's web portal, we used the [Sammy.js](http://sammyjs.org/), [Knockout](http://knockoutjs.com/index.html), and [jQuery](http://jquery.com/) libraries. We implemented dependency visualization using [mbostock](https://github.com/mbostock)'s [D3.js](http://d3js.org/) library, and we provide users with formatted XML in our server configuration tool using [vkiryukhin](https://github.com/vkiryukhin)'s elegant  [vkBeautify](http://www.eslinstructor.net/vkbeautify/) formatter.

## Motivation

The concept behind the whole project is that certain applications require specific resources in order to start correctly. App1 may need App2 to be running, for example. We manage this complexity by representing every application as a node in ZooKeeper. We then set watches (A ZooKeeper concept) on the nodes each application requires. When these nodes are created or destroyed, the watch triggers a callback within the agent. In this manner, applications will not start until they are ready to, and will do so automatically.

## System Requirements and Prerequisites

It's assumed that you are familiar with [Apache](https://github.com/apache)'s [ZooKeeper](https://github.com/apache/zookeeper) and the basics of administering it. Lots of useful information regarding ZooKeeper can be found in the [ZooKeeper Administrator's Guide](http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering). 

To use Zoom, you must have [Python](https://www.python.org/) installed. For your convenience, we have provided a ```bootstrap.sh``` file in ```sentinel/agent/scripts/``` which uses Python's ```easy_install``` module to include the ```python-ldap```, ```tornado```, ```kazoo```, ```setproctitle```, ```requests```, and ```pyodbc``` Python packages. 


## Goals

Why are we open-sourcing? Read about at Spot's engineering blog [here](http://www.spottradingllc.com/hello-world/).
