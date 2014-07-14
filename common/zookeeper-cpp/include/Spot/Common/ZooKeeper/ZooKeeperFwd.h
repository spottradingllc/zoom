#ifndef ZOO_KEEPER_FWD_H
#define ZOO_KEEPER_FWD_H

#include <string>
#include <utility>
#include <vector>


namespace Spot { namespace Common { namespace ZooKeeper
{
  typedef std::pair< std::string, bool > ZooKeeperStringResult;
  typedef std::pair< std::vector< std::string >, bool > ZooKeeperStringVectorResult;

} } } // namespaces

#endif
