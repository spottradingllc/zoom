# Zoom

Zoom is a platform created by Spot Trading to manage real-time application startup, configuration and dependency management. Zoom provides a server-side agent and front-end web interface to allow for easy administration of our software infrastructure.

## About

- Describe the backend Zookeeper agent.
- Describe the web front end.
- Describe the technologies used (i.e. Apache Zookeeper, Tornado, web frameworks/JavaScript libraries).

Zoom's web front-end is powered by [Tornado Web](https://github.com/tornadoweb)'s [Tornado](https://github.com/tornadoweb/tornado) web server. Our web interface was designed using Twitter's [Bootstrap](http://getbootstrap.com/) framework. In implementing Zoom's front-end, we used a handful of open-source JavaScript libraries. We simplified the inclusion and handling of these modules using [jrburke](https://github.com/jrburke)'s [RequireJS](http://requirejs.org/) library. To support real-time updates to Zoom's web portal, we used the [Sammy.js](http://sammyjs.org/), [Knockout](http://knockoutjs.com/index.html), and [jQuery](http://jquery.com/) libraries. We implemented dependency visualization using [mbostock](https://github.com/mbostock)'s [D3.js](http://d3js.org/) library, and we provide users with formatted XML in our server configuration tool using [vkiryukhin](https://github.com/vkiryukhin)'s elegant  [vkBeautify](http://www.eslinstructor.net/vkbeautify/) formatter.

## Motivation


## System Requirements and Prerequisites

It's assumed that you are familiar with [Apache](https://github.com/apache)'s [ZooKeeper](https://github.com/apache/zookeeper) and the basics of administering it. Lots of useful information regarding ZooKeeper can be found in the [ZooKeeper Administrator's Guide](http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering). 

To use Zoom, you must have [Python](https://www.python.org/) installed. For your convenience, we have provided a ```bootsrap.sh``` file in ```agent/scripts/``` which uses Python's ```easy_install``` module to include the ```python-ldap```, ```tornado```, ```kazoo```, ```setproctitle```, ```requests```, and ```pyodbc``` Python packages. 


## Goals

- Describe why we open-sourced the project and what we hope to bring about by collaborating with the GitHub community.

