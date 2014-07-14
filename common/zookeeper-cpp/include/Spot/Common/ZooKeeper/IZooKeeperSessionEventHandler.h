#ifndef IZOO_KEEPER_SESSION_EVENT_HANDLER_H
#define IZOO_KEEPER_SESSION_EVENT_HANDLER_H

#include <string>

#include "Spot/Common/Utility/Unused.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  class IZooKeeperSessionEventHandler
  {
  public:
    virtual ~IZooKeeperSessionEventHandler() noexcept {}

    virtual void OnConnecting( const std::string& host ) { unused( host ); }
    virtual void OnConnected( const std::string& host ) { unused( host ); }
    virtual void OnAssociating( const std::string& host ) { unused( host ); }
    virtual void OnExpiredSession( const std::string& host ) { unused( host ); }
  };

} } } // namespaces

#endif
