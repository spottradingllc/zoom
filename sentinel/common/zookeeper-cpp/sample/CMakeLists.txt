project(zookeeeper-sample)
cmake_minimum_required(VERSION 2.8)

set(CMAKE_COLOR_MAKEFILE ON)
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_INCLUDE_CURRENT_DIR TRUE)

set(SOURCE_LIST
    "main.cpp"
    "TestHarness.cpp"
    "TestHarness.h"
    "ITest.h"
    "TestAddEphemeralNodeEventHandlerWhenNodeCreated.h"
    "TestAddEphemeralNodeEventHandlerWhenNodeCreated.cpp"
    "TestAddPersistentNodeEventHandlerWhenNodeCreated.h"
    "TestAddPersistentNodeEventHandlerWhenNodeCreated.cpp"
    "TestAddEphemeralNodeEventHandlerWhenNodeDeleted.h"
    "TestAddEphemeralNodeEventHandlerWhenNodeDeleted.cpp"
    "TestChangeEphemeralNodeAndCompare.cpp"
    "TestChangeEphemeralNodeAndCompare.h"
    "TestChangePersistentNodeAndCompare.cpp"
    "TestChangePersistentNodeAndCompare.h"
    "TestChangeSequentialEphemeralNodeAndCompare.cpp"
    "TestChangeSequentialEphemeralNodeAndCompare.h"
    "TestChangeSequentialPersistentNodeAndCompare.cpp"
    "TestChangeSequentialPersistentNodeAndCompare.h"
    "TestCreateEphemeralNodeAndCompare.cpp"
    "TestCreateEphemeralNodeAndCompare.h"
    "TestCreatePersistentNodeAndCompare.cpp"
    "TestCreatePersistentNodeAndCompare.h"
    "TestCreateSequentialEphemeralNodeAndCompare.cpp"
    "TestCreateSequentialEphemeralNodeAndCompare.h"
    "TestCreateSequentialPersistentNodeAndCompare.cpp"
    "TestCreateSequentialPersistentNodeAndCompare.h"
    "TestGetNodeChildrenWhenNodeDoesNotExist.cpp"
    "TestGetNodeChildrenWhenNodeDoesNotExist.h"
    "TestGetNodeChildrenWhenNodeExistsButNoChildren.cpp"
    "TestGetNodeChildrenWhenNodeExistsButNoChildren.h"
    "TestGetNodeChildrenWhenChildNodeIsPersistent.cpp"
    "TestGetNodeChildrenWhenChildNodeIsPersistent.h"
    "TestGetNodeChildrenWhenChildNodeIsEphemeral.cpp"
    "TestGetNodeChildrenWhenChildNodeIsEphemeral.h"
    "TestGetNodeWhenNodeDoesNotExist.cpp"
    "TestGetNodeWhenNodeDoesNotExist.h"
    "TestGetNodeWhenNodeExistsButDataIsEmpty.cpp"
    "TestGetNodeWhenNodeExistsButDataIsEmpty.h")

add_executable(${PROJECT_NAME} ${SOURCE_LIST})

# set compiler flags
set(CMAKE_CXX_COMPILER "/spot/dev/3rdParty/cpp/gnu/gcc/gcc-4.7.3/bin/g++")
list(APPEND CMAKE_CXX_FLAGS "-std=c++11 -pthread -g -DNDEBUG -D_GLIBCXX_USE_NANOSLEEP -Wall -Wextra -pedantic-errors ${CMAKE_CXX_FLAGS}")

# set path to local includes
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/../include")

# set path to 3rd-party includes
include_directories(
    "/spot/dev/3rdParty/cpp/apache/apr/apr-1.4.8/gcc-4.7.3/include"
    "/spot/dev/3rdParty/cpp/apache/apr-util/apr-util-1.5.2/gcc-4.7.3/include"
    "/spot/dev/3rdParty/cpp/apache/log4cxx/log4cxx-0.10.0/gcc-4.7.3/include"
    "/spot/dev/3rdParty/cpp/apache/zookeeper/zookeeper-3.4.6/gcc-4.7.3/include"
    "/spot/dev/3rdParty/cpp/boost/boost-1.55.0/gcc-4.7.3/include")

# set path to local libraries
link_directories("${CMAKE_CURRENT_SOURCE_DIR}/../lib")

# set path to 3rd-party libraries
link_directories(
    "/spot/dev/3rdParty/cpp/apache/apr/apr-1.4.8/gcc-4.7.3/lib"
    "/spot/dev/3rdParty/cpp/apache/apr-util/apr-util-1.5.2/gcc-4.7.3/lib"
    "/spot/dev/3rdParty/cpp/apache/log4cxx/log4cxx-0.10.0/gcc-4.7.3/lib"
    "/spot/dev/3rdParty/cpp/apache/zookeeper/zookeeper-3.4.6/gcc-4.7.3/lib"
    "/spot/dev/3rdParty/cpp/boost/boost-1.55.0/gcc-4.7.3/lib")

# include 3rd-party libraries
add_library(apache-apr STATIC IMPORTED)
set_target_properties(apache-apr PROPERTIES IMPORTED_LOCATION "/spot/dev/3rdParty/cpp/apache/apr/apr-1.4.8/gcc-4.7.3/lib/libapr-1.a")

add_library(apache-apr-util STATIC IMPORTED)
set_target_properties(apache-apr-util PROPERTIES IMPORTED_LOCATION "/spot/dev/3rdParty/cpp/apache/apr-util/apr-util-1.5.2/gcc-4.7.3/lib/libaprutil-1.a")

add_library(apache-log4cxx STATIC IMPORTED)
set_target_properties(apache-log4cxx PROPERTIES IMPORTED_LOCATION "/spot/dev/3rdParty/cpp/apache/log4cxx/log4cxx-0.10.0/gcc-4.7.3/lib/liblog4cxx.a")

add_library(apache-zookeeper STATIC IMPORTED)
set_target_properties(apache-zookeeper PROPERTIES IMPORTED_LOCATION "/spot/dev/3rdParty/cpp/apache/zookeeper/zookeeper-3.4.6/gcc-4.7.3/lib/libzookeeper_mt.a")

add_library(boost STATIC IMPORTED)
set_target_properties(boost PROPERTIES IMPORTED_LOCATION "/spot/dev/3rdParty/cpp/boost/boost-1.55.0/gcc-4.7.3/lib/libboost_program_options.a")

add_library(spot-zookeeper STATIC IMPORTED)
set_target_properties(spot-zookeeper PROPERTIES IMPORTED_LOCATION "/home/david.shrader/linux/development/devops/service-registration-poc/configuration-cpp/lib/libSpot.Common.ZooKeeper.a")

target_link_libraries(${PROJECT_NAME} spot-zookeeper apache-log4cxx apache-apr apache-apr-util apache-zookeeper pthread expat boost)
