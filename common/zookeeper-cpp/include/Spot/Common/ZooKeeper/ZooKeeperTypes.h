#ifndef ZOO_KEEPER_TYPES_H
#define ZOO_KEEPER_TYPES_H

#include <cstdint>


namespace Spot { namespace Common { namespace ZooKeeper
{
  enum class ZooKeeperNodeType : std::int8_t
  {
    PERSISTENT = 1,
    EPHEMERAL = 2
  };

} } } // namespaces

#endif
