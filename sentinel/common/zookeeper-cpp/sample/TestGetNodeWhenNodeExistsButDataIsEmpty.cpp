#include "TestGetNodeWhenNodeExistsButDataIsEmpty.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestGetNodeWhenNodeExistsButDataIsEmpty::TestGetNodeWhenNodeExistsButDataIsEmpty( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestGetNodeWhenNodeExistsButDataIsEmpty::~TestGetNodeWhenNodeExistsButDataIsEmpty() noexcept
  {
  }


  void TestGetNodeWhenNodeExistsButDataIsEmpty::StartUp()
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


  void TestGetNodeWhenNodeExistsButDataIsEmpty::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "";

    try
    {
      bool r1 = m_zooKeeper->CreateNode( path, data, ZooKeeper::ZooKeeperNodeType::EPHEMERAL );
      if( r1 )
      {
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % path % data ) );

        ZooKeeper::ZooKeeperStringResult r2 = m_zooKeeper->GetNode( path );
        if( r2.second )
        {
          if( r2.first == data )
          {
            LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> queried with data <%s>" ) % path % data ) );

            result = true;

            LOGGER_INFO( m_logger, "Test PASSED" );
          }
        }
      }
    }
    catch( const std::exception& ex )
    {
      LOGGER_ERROR( m_logger, ex.what() );
    }

    if( !result )
    {
      LOGGER_ERROR( m_logger, "Test FAILED" );
    }
  }


  void TestGetNodeWhenNodeExistsButDataIsEmpty::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestGetNodeWhenNodeExistsButDataIsEmpty::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
