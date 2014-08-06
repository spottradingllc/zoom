#ifndef ZOO_KEEPER_EVENT_H
#define ZOO_KEEPER_EVENT_H

#include <zookeeper/zookeeper.h>


namespace Spot { namespace Common { namespace ZooKeeper
{
  class ZooKeeperEvent
  {
  public:
    static void EventHandler( zhandle_t* zhandle, int type, int state, const char* path, void* userData );
  };

} } } // namespaces

#endif
