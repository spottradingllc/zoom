#include "TestAddPersistentNodeEventHandlerWhenNodeCreated.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestAddPersistentNodeEventHandlerWhenNodeCreated::TestAddPersistentNodeEventHandlerWhenNodeCreated( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestAddPersistentNodeEventHandlerWhenNodeCreated::~TestAddPersistentNodeEventHandlerWhenNodeCreated() noexcept
  {
  }


  void TestAddPersistentNodeEventHandlerWhenNodeCreated::StartUp()
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


  void TestAddPersistentNodeEventHandlerWhenNodeCreated::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, powdered";

    try
    {
      m_zooKeeper->AddNodeEventHandler( path, this );
      LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> event handler created" ) % path ) );

      bool r1 = m_zooKeeper->CreateNode( path, data, ZooKeeper::ZooKeeperNodeType::PERSISTENT );
      if( r1 )
      {
        Lock lock( m_mutex );
        if( m_condition.wait_for( lock, std::chrono::seconds( 5 ) ) == std::cv_status::timeout )
        {
          LOGGER_ERROR( m_logger, boost::str( boost::format( "Node <%s> event handler timeout" ) % path ) );
        }
        else
        {
          m_zooKeeper->RemoveNodeEventHandler( path );

          m_zooKeeper->DeleteNode( path );
          LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> deleted" ) % path ) );

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


  void TestAddPersistentNodeEventHandlerWhenNodeCreated::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestAddPersistentNodeEventHandlerWhenNodeCreated::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }


  void TestAddPersistentNodeEventHandlerWhenNodeCreated::OnNodeCreated( const std::string& path )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created" ) % path ) );

    m_condition.notify_all();
  }

} // namespace
