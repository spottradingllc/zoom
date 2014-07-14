#ifndef IZOO_KEEPER_NODE_EVENT_HANDLER_H
#define IZOO_KEEPER_NODE_EVENT_HANDLER_H

#include <string>

#include "Spot/Common/Utility/Unused.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  class IZooKeeperNodeEventHandler
  {
  public:
    virtual ~IZooKeeperNodeEventHandler() noexcept {}

    virtual void OnNodeCreated( const std::string& path ) { unused( path ); }
    virtual void OnNodeChanged( const std::string& path ) { unused( path ); }
    virtual void OnNodeChildrenChanged( const std::string& path ) { unused( path ); }
    virtual void OnNodeDeleted( const std::string& path ) { unused( path ); }
  };

} } } // namespaces

#endif
