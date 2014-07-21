Zoom
========
Zoom is the "Zookeeper Manager" project created by Spot Trading, LLC. Inspired by [Netflix](https://github.com/Netflix)'s [Exhibitor](https://github.com/Netflix/exhibitor), Zoom provides a server-side agent and front-end user interface to allow for easy administration of services across a Zookeeper instance.

## About

According to the "ZooKeeper documentation":http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering

bq. You will want to have a supervisory process that manages each of your ZooKeeper server processes (JVM).

Exhibitor is a Java supervisor system for ZooKeeper. It provides a number of features:
* Watches a ZK instance and makes sure it is running
* Performs periodic backups
* Perform periodic cleaning of ZK log directory
* A GUI explorer for viewing ZK nodes
* A rich REST API

## Motivation



## System Requirements and Prerequisites

* It's assumed that you are familiar with ZooKeeper and the basics of administering it (see the "ZooKeeper Administrator's Guide":http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering for details).
* Exhibitor is a Java-based application
* Exhibitor is designed to be run on Unix/Linux based systems (as is Apache ZooKeeper).
* The java CLI tool <code>jps</code> must be in the command line PATH.

## Goals
