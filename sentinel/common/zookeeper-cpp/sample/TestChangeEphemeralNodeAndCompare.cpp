#include "TestChangeEphemeralNodeAndCompare.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestChangeEphemeralNodeAndCompare::TestChangeEphemeralNodeAndCompare( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestChangeEphemeralNodeAndCompare::~TestChangeEphemeralNodeAndCompare() noexcept
  {
  }


  void TestChangeEphemeralNodeAndCompare::StartUp()
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


  void TestChangeEphemeralNodeAndCompare::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, powdered";

    try
    {
      bool r1 = m_zooKeeper->CreateNode( path, data, ZooKeeper::ZooKeeperNodeType::EPHEMERAL );
      if( r1 )
      {
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % path % data ) );

        data = "glazed, chocolate, bear claw";
        m_zooKeeper->ChangeNode( path, data );
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> changed with data <%s>" ) % path % data ) );

        ZooKeeper::ZooKeeperStringResult r2 = m_zooKeeper->GetNode( path );
        if( r2.second )
        {
          if( r2.first == data )
          {
            LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> validated with data <%s>" ) % path % data ) );

            result = true;
          }
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


  void TestChangeEphemeralNodeAndCompare::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestChangeEphemeralNodeAndCompare::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
