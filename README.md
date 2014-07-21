Zoom
========
Zoom is the "ZooKeeper Manager" project created by Spot Trading, LLC's DevOps team. Inspired by [Netflix](https://github.com/Netflix)'s [Exhibitor](https://github.com/Netflix/exhibitor), Zoom provides a server-side agent and front-end user interface to allow for easy administration of services across a ZooKeeper instance.

## About

- Describe the Zookeeper agent.
- Describe the web frontend.
- Describe the technologies used (ie. Zookeeper, Tornado, web frameworks/JavaScript libraries).

## Motivation

- Describe why we chose ZooKeeper and why we decided to write our own manager for ZooKeeper instances.


## System Requirements and Prerequisites

It's assumed that you are familiar with [Apache](https://github.com/apache)'s [ZooKeeper](https://github.com/apache/zookeeper) and the basics of administering it. Lots of useful information regarding ZooKeeper can be found in the [ZooKeeper Administrator's Guide](http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering). 

For your convenience, we have provided a ```bootsrap.sh``` file in ```agent/scripts/``` which uses Python's ```easy_install``` module to include the ```python-ldap```, ```tornado```, ```kazoo```, ```setproctitle```, ```requests```, and ```pyodbc``` Python packages. 


## Goals

- Describe why we open-sourced the project and what we hope to bring about by collaborating with the GitHub community.
