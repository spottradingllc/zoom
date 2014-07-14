#include "TestChangeSequentialEphemeralNodeAndCompare.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestChangeSequentialEphemeralNodeAndCompare::TestChangeSequentialEphemeralNodeAndCompare( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestChangeSequentialEphemeralNodeAndCompare::~TestChangeSequentialEphemeralNodeAndCompare() noexcept
  {
  }


  void TestChangeSequentialEphemeralNodeAndCompare::StartUp()
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


  void TestChangeSequentialEphemeralNodeAndCompare::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, powdered";

    try
    {
      std::string sequentialPath = m_zooKeeper->CreateSequentialNode( path, data, ZooKeeper::ZooKeeperNodeType::EPHEMERAL );
      LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % sequentialPath % data ) );

      data = "glazed, chocolate, bear claw";
      m_zooKeeper->ChangeNode( sequentialPath, data );
      LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> changed with data <%s>" ) % sequentialPath % data ) );

      ZooKeeper::ZooKeeperStringResult r2 = m_zooKeeper->GetNode( sequentialPath );
      if( r2.second )
      {
        if( r2.first == data )
        {
          LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> validated with data <%s>" ) % sequentialPath % data ) );

          result = true;
        }
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


  void TestChangeSequentialEphemeralNodeAndCompare::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestChangeSequentialEphemeralNodeAndCompare::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
