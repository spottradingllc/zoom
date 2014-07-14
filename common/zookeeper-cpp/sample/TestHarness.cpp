#include "TestHarness.h"

#include <boost/format.hpp>

#include "Spot/Common/Logger/Log4cxxLogger.h"
#include "Spot/Common/Utility/System.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"

#include "TestAddEphemeralNodeEventHandlerWhenNodeCreated.h"
#include "TestAddPersistentNodeEventHandlerWhenNodeCreated.h"
#include "TestAddEphemeralNodeEventHandlerWhenNodeDeleted.h"
#include "TestChangeEphemeralNodeAndCompare.h"
#include "TestChangePersistentNodeAndCompare.h"
#include "TestChangeSequentialEphemeralNodeAndCompare.h"
#include "TestChangeSequentialPersistentNodeAndCompare.h"
#include "TestCreatePersistentNodeAndCompare.h"
#include "TestCreateEphemeralNodeAndCompare.h"
#include "TestCreateSequentialPersistentNodeAndCompare.h"
#include "TestCreateSequentialEphemeralNodeAndCompare.h"
#include "TestGetNodeChildrenWhenChildNodeIsPersistent.h"
#include "TestGetNodeChildrenWhenChildNodeIsEphemeral.h"
#include "TestGetNodeChildrenWhenNodeDoesNotExist.h"
#include "TestGetNodeChildrenWhenNodeExistsButNoChildren.h"
#include "TestGetNodeWhenNodeDoesNotExist.h"
#include "TestGetNodeWhenNodeExistsButDataIsEmpty.h"


namespace Spot
{
  TestHarness::TestHarness( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder )
  {
    m_logger = new Logger::Log4cxxLogger();
    m_zooKeeper = new ZooKeeper::ZooKeeper( host, connectionTimeout, sessionExpirationTimeout, deterministicConnectionOrder );

    m_logger->Initialize( "log4cxx.config.xml" );
    m_zooKeeper->RegisterLogger( m_logger );

    m_tests.push_back( ITestPtr( new TestCreatePersistentNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestCreateEphemeralNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestCreateSequentialPersistentNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestCreateSequentialEphemeralNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeChildrenWhenNodeDoesNotExist( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeChildrenWhenNodeExistsButNoChildren( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeWhenNodeDoesNotExist( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeWhenNodeExistsButDataIsEmpty( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestChangeEphemeralNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestChangePersistentNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestChangeSequentialEphemeralNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestChangeSequentialPersistentNodeAndCompare( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeChildrenWhenChildNodeIsPersistent( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestGetNodeChildrenWhenChildNodeIsEphemeral( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestAddEphemeralNodeEventHandlerWhenNodeCreated( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestAddPersistentNodeEventHandlerWhenNodeCreated( m_logger, m_zooKeeper ) ) );
    m_tests.push_back( ITestPtr( new TestAddEphemeralNodeEventHandlerWhenNodeDeleted( m_logger, m_zooKeeper ) ) );
  }


  TestHarness::~TestHarness() noexcept
  {
    if( m_zooKeeper != nullptr )
    {
      m_zooKeeper->UnregisterLogger();

      delete m_zooKeeper;

      if( m_logger != nullptr )
      {
        m_logger->Uninitialize();

        delete m_logger;
      }
    }
  }


  void TestHarness::Run()
  {
    for( ITestPtr& testPtr : m_tests )
    {
      testPtr->StartUp();
      testPtr->Execute();
      testPtr->TearDown();
    }
  }

} // namespace
