#include "TestGetNodeChildrenWhenChildNodeIsPersistent.h"

#include <boost/format.hpp>

#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot
{
  TestGetNodeChildrenWhenChildNodeIsPersistent::TestGetNodeChildrenWhenChildNodeIsPersistent( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper ) :
    m_logger( logger ),
    m_zooKeeper( zooKeeper )
  {
  }


  TestGetNodeChildrenWhenChildNodeIsPersistent::~TestGetNodeChildrenWhenChildNodeIsPersistent() noexcept
  {
  }


  void TestGetNodeChildrenWhenChildNodeIsPersistent::StartUp()
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


  void TestGetNodeChildrenWhenChildNodeIsPersistent::Execute()
  {
    bool result = false;

    std::string path = "/zookeeper/doughnuts";
    std::string data = "glazed, chocolate, munchkins";

    std::string childpath1 = "/zookeeper/doughnuts/ingredients";
    std::string childdata1 = "flour, sugar, marijuana";

    std::string childpath2 = "/zookeeper/doughnuts/cost";
    std::string childdata2 = "$6/half-dozen, $11/dozen, $11.50/bakers dozen *(5x price for marijuana doughnuts)";

    try
    {
      bool r1 = m_zooKeeper->CreateNode( path, data, ZooKeeper::ZooKeeperNodeType::PERSISTENT );
      if( r1 )
      {
        LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> created with data <%s>" ) % path % data ) );

        bool c1 = m_zooKeeper->CreateNode( childpath1, childdata1, ZooKeeper::ZooKeeperNodeType::PERSISTENT );
        if( c1 )
        {
          LOGGER_INFO( m_logger, boost::str( boost::format( "Child node <%s> created with data <%s>" ) % childpath1 % childdata1 ) );

          bool c2 = m_zooKeeper->CreateNode( childpath2, childdata2, ZooKeeper::ZooKeeperNodeType::PERSISTENT );
          if( c2 )
          {
            LOGGER_INFO( m_logger, boost::str( boost::format( "Child node <%s> created with data <%s>" ) % childpath2 % childdata2 ) );

            ZooKeeper::ZooKeeperStringVectorResult r2 = m_zooKeeper->GetNodeChildren( path );
            if( r2.second && (r2.first.size() == 2) )
            {
              auto children = r2.first;
              for( const std::string& child : children )
              {
                std::string node = path + "/" + child;

                LOGGER_INFO( m_logger, boost::str( boost::format( "Child node <%s> validated" ) % node ) );

                m_zooKeeper->DeleteNode( node );
                LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> deleted" ) % node ) );
              }

              m_zooKeeper->DeleteNode( path );
              LOGGER_INFO( m_logger, boost::str( boost::format( "Node <%s> deleted" ) % path ) );

              result = true;
            }
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


  void TestGetNodeChildrenWhenChildNodeIsPersistent::TearDown()
  {
    m_zooKeeper->UnregisterSessionEventHandler();
    m_zooKeeper->Uninitialize();
  }


  void TestGetNodeChildrenWhenChildNodeIsPersistent::OnConnected( const std::string& host )
  {
    LOGGER_INFO( m_logger, boost::str( boost::format( "Session <%s> connected" ) % host ) );

    m_condition.notify_all();
  }

} // namespace
