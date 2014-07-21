# Zoom

Zoom is the "ZooKeeper Manager" project created by Spot Trading, LLC's DevOps team. Inspired by [Netflix](https://github.com/Netflix)'s [Exhibitor](https://github.com/Netflix/exhibitor), Zoom provides a server-side agent and front-end user interface to allow for easy administration of services across a ZooKeeper instance.

## About

- Describe the backend Zookeeper agent.
- Describe the web frontend.
- Describe the technologies used (ie. Zookeeper, Tornado, web frameworks/JavaScript libraries).

Zoom's web front-end is powered by [Tornadoweb](https://github.com/tornadoweb)'s [Tornado](https://github.com/tornadoweb/tornado) web server. Our web interface was designed using Twitter's [Bootstrap](http://getbootstrap.com/) framework. In implementing Zoom's front-end, we used a handful of open-source JavaScript libraries. We simplified the inclusion and handling of these modules using [jrburke](https://github.com/jrburke)'s [RequireJS](http://requirejs.org/) library. To support real-time updates to Zoom's web portal, we used the [Sammy.js](http://sammyjs.org/), [Knockout](http://knockoutjs.com/index.html), and [jQuery](http://jquery.com/) libraries. We implemented dependency visualization using [mbostock](https://github.com/mbostock)'s [D3.js](http://d3js.org/) library, and we provide users with formatted XML in our server configuration tool using [vkiryukhin](https://github.com/vkiryukhin)'s elegant  [vkBeautify](http://www.eslinstructor.net/vkbeautify/) formatter.

## Motivation


## System Requirements and Prerequisites

It's assumed that you are familiar with [Apache](https://github.com/apache)'s [ZooKeeper](https://github.com/apache/zookeeper) and the basics of administering it. Lots of useful information regarding ZooKeeper can be found in the [ZooKeeper Administrator's Guide](http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering). 

To use Zoom, you must have [Python](https://www.python.org/) installed. For your convenience, we have provided a ```bootsrap.sh``` file in ```agent/scripts/``` which uses Python's ```easy_install``` module to include the ```python-ldap```, ```tornado```, ```kazoo```, ```setproctitle```, ```requests```, and ```pyodbc``` Python packages. 


## Goals

- Describe why we open-sourced the project and what we hope to bring about by collaborating with the GitHub community.

