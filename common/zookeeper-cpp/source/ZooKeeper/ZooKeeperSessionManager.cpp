#include "ZooKeeperSessionManager.h"

#include <errno.h>
#include <string.h>

#include <boost/format.hpp>

#include "Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"

#include "ZooKeeperEvent.h"
#include "ZooKeeperException.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  ZooKeeperSessionManager::ZooKeeperSessionManager( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder ) :
    m_host( host ),
    m_connectionTimeout( connectionTimeout ),
    m_expirationTimeout( sessionExpirationTimeout ),
    m_deterministicConnectionOrder( deterministicConnectionOrder ),
    m_handle( nullptr ),
    m_isInitialized( false )
  {
    zoo_deterministic_conn_order( deterministicConnectionOrder );
  }


  ZooKeeperSessionManager::~ZooKeeperSessionManager() noexcept
  {
  }


  void ZooKeeperSessionManager::Initialize()
  {
    if( m_isInitialized )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> already initialized" ) % m_host ) );
    }

    // convert expiration timeout from seconds to milliseconds
    int sessionExpirationTimeout = m_expirationTimeout * 1000;

    m_handle = zookeeper_init( m_host.c_str(), ZooKeeperEvent::EventHandler, sessionExpirationTimeout, 0, this, 0 );
    if( m_handle == NULL )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> failed to initialize with errno <%d>" ) % m_host % errno ) );
    }

    // wait for connection (or expiration timeout)
    Lock lock( m_sessionMutex );
    if( m_condition.wait_for( lock, std::chrono::seconds( m_connectionTimeout ) ) == std::cv_status::timeout )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> connection timeout" ) % m_host ) );
    }

    m_isInitialized = true;
  }


  void ZooKeeperSessionManager::Uninitialize()
  {
    if( !m_isInitialized )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> not initialized" ) % m_host ) );
    }

    if( m_handle != nullptr )
    {
      // can block as session flushes outstanding requests
      int result = zookeeper_close( m_handle );
      if( result != ZOK )
      {
        throw ZooKeeperException( result );
      }
    }

    m_isInitialized = false;
  }


  void ZooKeeperSessionManager::RegisterEventHandler( IZooKeeperSessionEventHandler* eventHandler )
  {
    Lock lock( m_clientMutex );

    if( m_eventHandler != nullptr )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> event handler already registered" ) % m_host ) );
    }

    m_eventHandler = eventHandler;
  }


  void ZooKeeperSessionManager::UnregisterEventHandler()
  {
    Lock lock( m_clientMutex );

    if( m_eventHandler == nullptr )
    {
      throw std::runtime_error( boost::str( boost::format( "Session <%s> event handler not registered" ) % m_host ) );
    }

    m_eventHandler = nullptr;
  }


  zhandle_t* ZooKeeperSessionManager::GetHandle() const noexcept
  {
    return m_handle;
  }


  const std::string& ZooKeeperSessionManager::GetHost() const noexcept
  {
    return m_host;
  }


  int ZooKeeperSessionManager::GetConnectionTimeout() const noexcept
  {
    return m_connectionTimeout;
  }


  int ZooKeeperSessionManager::GetExpirationTimeout() const noexcept
  {
    return m_expirationTimeout;
  }


  int ZooKeeperSessionManager::GetDeterministicConnectionOrder() const noexcept
  {
    return m_deterministicConnectionOrder;
  }


  void ZooKeeperSessionManager::FireEvent( zhandle_t* zhandle, int state )
  {
    unused( zhandle );

    if( state == ZOO_CONNECTED_STATE )
    {
      m_condition.notify_all();
    }
    else if( state == ZOO_EXPIRED_SESSION_STATE )
    {
      // reconnect
    }

    // fire client session event handler
    Lock lock( m_clientMutex );

    if( m_eventHandler != nullptr )
    {
      if( state == ZOO_CONNECTING_STATE )
      {
        m_eventHandler->OnConnecting( m_host );
      }
      else if( state == ZOO_CONNECTED_STATE )
      {
        m_eventHandler->OnConnected( m_host );
      }
      else if( state == ZOO_ASSOCIATING_STATE )
      {
        m_eventHandler->OnAssociating( m_host );
      }
      else if( state == ZOO_EXPIRED_SESSION_STATE )
      {
        m_eventHandler->OnExpiredSession( m_host );
      }
    }
  }

} } } // namespaces
