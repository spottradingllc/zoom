#include "ZooKeeperEvent.h"

#include "ZooKeeperNodeManager.h"
#include "ZooKeeperSessionManager.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  void ZooKeeperEvent::EventHandler( zhandle_t* zhandle, int type, int state, const char* path, void* userData )
  {
    if( userData != nullptr )
    {
      if( type == ZOO_SESSION_EVENT )
      {
        ZooKeeperSessionManager* zooKeeperSessionManager = reinterpret_cast< ZooKeeperSessionManager* >( userData );
        zooKeeperSessionManager->FireEvent( zhandle, state );
      }
      else
      {
        ZooKeeperNodeManager* zooKeeperNodeManager = reinterpret_cast< ZooKeeperNodeManager* >( userData );
        zooKeeperNodeManager->FireEvent( zhandle, type, state, path );
      }
    }    
  }

} } } // namespaces
