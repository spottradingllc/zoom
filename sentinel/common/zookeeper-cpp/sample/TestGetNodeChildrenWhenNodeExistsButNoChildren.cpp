#include "TestGetNodeChildrenWhenNodeExistsButNoChildren.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestGetNodeChildrenWhenNodeExistsButNoChildren::TestGetNodeChildrenWhenNodeExistsButNoChildren( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestGetNodeChildrenWhenNodeExistsButNoChildren::~TestGetNodeChildrenWhenNodeExistsButNoChildren() noexcept
  {
  }


  void TestGetNodeChildrenWhenNodeExistsButNoChildren::StartUp()
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


  void TestGetNodeChildrenWhenNodeExistsButNoChildren::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, munchkins";

    try
    {
      bool r1 = m_zooKeeper->CreateNode( path, data, ZooKeeper::ZooKeeperNodeType::EPHEMERAL );
      if( r1 )
      {
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % path % data ) );

        ZooKeeper::ZooKeeperStringVectorResult r2 = m_zooKeeper->GetNodeChildren( path );
        if( r2.second && (r2.first.size() == 0) )
        {
          LOGGER_INFO( m_logger, boost::str( boost::format( "Node children <%s> do not exist" ) % path ) );

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


  void TestGetNodeChildrenWhenNodeExistsButNoChildren::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestGetNodeChildrenWhenNodeExistsButNoChildren::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
