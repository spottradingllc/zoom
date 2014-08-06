#include "TestCreateSequentialPersistentNodeAndCompare.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestCreateSequentialPersistentNodeAndCompare::TestCreateSequentialPersistentNodeAndCompare( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestCreateSequentialPersistentNodeAndCompare::~TestCreateSequentialPersistentNodeAndCompare() noexcept
  {
  }


  void TestCreateSequentialPersistentNodeAndCompare::StartUp()
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


  void TestCreateSequentialPersistentNodeAndCompare::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, sprinkles";

    try
    {
      std::string sequentialPath = m_zooKeeper->CreateSequentialNode( path, data, ZooKeeper::ZooKeeperNodeType::PERSISTENT );
      LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % sequentialPath % data ) );

      m_zooKeeper->DeleteNode( sequentialPath );
      LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> deleted" ) % sequentialPath ) );

      result = true;
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


  void TestCreateSequentialPersistentNodeAndCompare::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestCreateSequentialPersistentNodeAndCompare::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
