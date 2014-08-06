#include "TestGetNodeWhenNodeDoesNotExist.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestGetNodeWhenNodeDoesNotExist::TestGetNodeWhenNodeDoesNotExist( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestGetNodeWhenNodeDoesNotExist::~TestGetNodeWhenNodeDoesNotExist() noexcept
  {
  }


  void TestGetNodeWhenNodeDoesNotExist::StartUp()
  {
    try
    {
      m_zooKeeper->RegisterSessionEventHandler( this );
      m_zooKeeper->Initialize();

      // wait for connection (or expiration timeout)
      Lock lock( m_mutex );
      if( m_condition.wait_for( lock, std::chrono::seconds( m_zooKeeper->GetConnectionTimeout() ) ) == std::cv_status::timeout )
      {
        LOGGER_ERROR( m_logger, "OnConnected never called" );
      }
    }
    catch( const std::exception& ex )
    {
      LOGGER_ERROR( m_logger, ex.what() );
    }
  }


  void TestGetNodeWhenNodeDoesNotExist::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/bagels";

    try
    {
      ZooKeeper::ZooKeeperStringResult r1 = m_zooKeeper->GetNode( path );
      if( !r1.second )
      {
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> does not exist" ) % path ) );

        result = true;
      }
    }
    catch( const std::exception& ex )
    {
      LOGGER_ERROR( m_logger, ex.what() );
    }

    if( result )
    {
      LOGGER_INFO( m_logger, "Test PASSED" );
    }
    else
    {
      LOGGER_ERROR( m_logger, "Test FAILED" );
    }
  }


  void TestGetNodeWhenNodeDoesNotExist::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestGetNodeWhenNodeDoesNotExist::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
