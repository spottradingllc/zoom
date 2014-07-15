zoom
====
h1. What is Exhibitor?

_Use links at right --------->_

According to the "ZooKeeper documentation":http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering

bq. You will want to have a supervisory process that manages each of your ZooKeeper server processes (JVM).

Exhibitor is a Java supervisor system for ZooKeeper. It provides a number of features:
* Watches a ZK instance and makes sure it is running
* Performs periodic backups
* Perform periodic cleaning of ZK log directory
* A GUI explorer for viewing ZK nodes
* A rich REST API

h1. Requirements/Prerequisites

* It's assumed that you are familiar with ZooKeeper and the basics of administering it (see the "ZooKeeper Administrator's Guide":http://zookeeper.apache.org/doc/trunk/zookeeperAdmin.html#sc_administering for details).
* Exhibitor is a Java-based application
* Exhibitor is designed to be run on Unix/Linux based systems (as is Apache ZooKeeper).
* The java CLI tool <code>jps</code> must be in the command line PATH.

h1. Maven / Artifacts

Exhibitor binaries are published to Maven Central.

|_.GroupID/Org|_.ArtifactID/Name|_.Description|
|com.netflix.exhibitor|exhibitor-standalone|Self-containing, runnable version of Exhibitor (as an application or a WAR file)|
|com.netflix.exhibitor|exhibitor-core|Library version of Exhibitor that can be integrated into your application|
