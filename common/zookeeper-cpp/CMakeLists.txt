cmake_minimum_required(VERSION 2.8)

project(Spot.Common.ZooKeeper)

set(CMAKE_COLOR_MAKEFILE ON)
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_INCLUDE_CURRENT_DIR TRUE)

set(SOURCE_LIST
    "include/Spot/Common/Application/IApplicationEventHandler.h"
    "include/Spot/Common/Logger/ILogger.h"
    "include/Spot/Common/Logger/ILoggerEventHandler.h"
    "include/Spot/Common/Logger/Log4cxxLogger.h"
    "include/Spot/Common/Utility/System.h"
    "include/Spot/Common/Utility/Unused.h"
    "include/Spot/Common/ZooKeeper/IZooKeeperNodeEventHandler.h"
    "include/Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"
    "include/Spot/Common/ZooKeeper/ZooKeeper.h"
    "include/Spot/Common/ZooKeeper/ZooKeeperFwd.h"
    "include/Spot/Common/ZooKeeper/ZooKeeperTypes.h"
    "source/Logger/Log4cxxLogger.cpp"
    "source/Utility/System.cpp"
    "source/ZooKeeper/ZooKeeper.cpp"
    "source/ZooKeeper/ZooKeeperEvent.cpp"
    "source/ZooKeeper/ZooKeeperEvent.h"
    "source/ZooKeeper/ZooKeeperException.cpp"
    "source/ZooKeeper/ZooKeeperException.h"
    "source/ZooKeeper/ZooKeeperImpl.cpp"
    "source/ZooKeeper/ZooKeeperImpl.h"
    "source/ZooKeeper/ZooKeeperNodeManager.cpp"
    "source/ZooKeeper/ZooKeeperNodeManager.h"
    "source/ZooKeeper/ZooKeeperSessionManager.cpp"
    "source/ZooKeeper/ZooKeeperSessionManager.h"
    "source/ZooKeeper/ZooKeeperStat.cpp"
    "source/ZooKeeper/ZooKeeperStat.h")

set( THIRD_PARTY "/spot/dev/3rdParty/cpp" )

set( APR_VERSION "1.4.8" )
set( APR_UTIL_VERSION "1.5.2" )
set( BOOST_VERSION "1.49.0" )
set( GCC_VERSION "4.7.3" )
set( LIBXML2_VERSION "2.7.7" )
set( LOG4CXX_VERSION "0.10.0" )
set( ZOOKEEPER_VERSION "3.4.6" )

set( BOOST_PATH "${THIRD_PARTY}/boost/boost-${BOOST_VERSION}/gcc-${GCC_VERSION}" )
set( LIBXML2_PATH "${THIRD_PARTY}/xmlsoft/libxml2/libxml2-${LIBXML2_VERSION}/gcc-${GCC_VERSION}" )
set( LOG4CXX_PATH "${THIRD_PARTY}/apache/log4cxx/log4cxx-${LOG4CXX_VERSION}/gcc-${GCC_VERSION}" )

# set the compiler flags
set(CMAKE_CXX_COMPILER "${THIRD_PARTY}/gnu/gcc/gcc-${GCC_VERSION}/bin/g++")
list(APPEND CMAKE_CXX_FLAGS "-std=c++11 -pthread -g -DNDEBUG -D_GLIBCXX_USE_NANOSLEEP -Wall -Wextra -pedantic-errors ${CMAKE_CXX_FLAGS}")

# set the path to internal headers
include_directories("./include")

# set the path to 3rd-party headers
include_directories(
    "${THIRD_PARTY}/apache/apr/${APR_VERSION}/gcc-${GCC_VERSION}/include"
    "${THIRD_PARTY}/apache/apr-util/apr-util-${APR_UTIL_VERSION}/gcc-${GCC_VERSION}/include"
    "${THIRD_PARTY}/apache/log4cxx/log4cxx-${LOG4CXX_VERSION}/gcc-${GCC_VERSION}/include"
    "${THIRD_PARTY}/apache/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/gcc-${GCC_VERSION}/include"
    "${THIRD_PARTY}/boost/boost-${BOOST_VERSION}/gcc-${GCC_VERSION}/include")

# set the path to 3rd-party library directory
link_directories(
    "${THIRD_PARTY}/apache/apr/apr-${APR_VERSION}/gcc-${GCC_VERSION}/lib"
    "${THIRD_PARTY}/apache/apr-util/apr-util-${APR_UTIL_VERSION}/gcc-${GCC_VERSION}/lib"
    "${THIRD_PARTY}/apache/log4cxx/log4cxx-${LOG4CXX_VERSION}/gcc-${GCC_VERSION}/lib"
    "${THIRD_PARTY}/apache/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/gcc-${GCC_VERSION}/lib"
    "${THIRD_PARTY}/boost/boost-${BOOST_VERSION}/gcc-${GCC_VERSION}/lib")

# add 3rd-party libraries
add_library(APACHE_APR STATIC IMPORTED)
set_target_properties(APACHE_APR PROPERTIES IMPORTED_LOCATION "${THIRD_PARTY}/apache/apr/apr-${APR_VERSION}/gcc-${GCC_VERSION}/lib/libapr-1.a")

add_library(APACHE_APR_UTIL STATIC IMPORTED)
set_target_properties(APACHE_APR_UTIL PROPERTIES IMPORTED_LOCATION "${THIRD_PARTY}/apache/apr-util/apr-util-${APR_UTIL_VERSION}/gcc-${GCC_VERSION}/lib/libaprutil-1.a")

add_library(APACHE_LOG4CXX STATIC IMPORTED)
set_target_properties(APACHE_LOG4CXX PROPERTIES IMPORTED_LOCATION "${THIRD_PARTY}/apache/log4cxx/log4cxx-${LOG4CXX_VERSION}/gcc-${GCC_VERSION}/lib/liblog4cxx.a")

add_library(APACHE_ZOOKEEPER STATIC IMPORTED)
set_target_properties(APACHE_ZOOKEEPER PROPERTIES IMPORTED_LOCATION "${THIRD_PARTY}/apache/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/gcc-${GCC_VERSION}/lib/libzookeeper_mt.a")

add_library(BOOST STATIC IMPORTED)
set_target_properties(BOOST PROPERTIES IMPORTED_LOCATION "${THIRD_PARTY}/boost/boost-${BOOST_VERSION}/gcc-${GCC_VERSION}/lib/libboost_program_options.a")

# create both static and shared libraries
add_library(${PROJECT_NAME}_SO SHARED ${SOURCE_LIST})
set_target_properties(${PROJECT_NAME}_SO PROPERTIES OUTPUT_NAME ${PROJECT_NAME})

add_library(${PROJECT_NAME}_A STATIC ${SOURCE_LIST})
set_target_properties(${PROJECT_NAME}_A PROPERTIES OUTPUT_NAME ${PROJECT_NAME})
