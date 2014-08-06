#ifndef TEST_ADD_EPHEMERAL_NODE_EVENT_HANDLER_WHEN_NODE_DELETED_H
#define TEST_ADD_EPHEMERAL_NODE_EVENT_HANDLER_WHEN_NODE_DELETED_H

#include <condition_variable>
#include <mutex>

#include "Spot/Common/Logger/ILogger.h"
#include "Spot/Common/ZooKeeper/IZooKeeperNodeEventHandler.h"
#include "Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"
#include "Spot/Common/ZooKeeper/ZooKeeper.h"

#include "ITest.h"


namespace Spot
{
  class TestAddEphemeralNodeEventHandlerWhenNodeDeleted final :
    public ITest,
    public ZooKeeper::IZooKeeperSessionEventHandler,
    public ZooKeeper::IZooKeeperNodeEventHandler
  {
  public:
    TestAddEphemeralNodeEventHandlerWhenNodeDeleted( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper );
    virtual ~TestAddEphemeralNodeEventHandlerWhenNodeDeleted() noexcept;

    // ITest interface
    virtual void StartUp() override ;
    virtual void Execute() override;
    virtual void TearDown() override;

  private:
    Logger::ILogger* m_logger;
    ZooKeeper::ZooKeeper* m_zooKeeper;

    typedef std::unique_lock< std::mutex > Lock;
    std::mutex m_mutex;

    std::condition_variable m_condition;

    // IZooKeeperSessionEventHandler interface
    virtual void OnConnected( const std::string& host ) override;

    // IZooKeeperNodeEventHandler interface
    virtual void OnNodeDeleted( const std::string& path ) override;
  };
}

#endif
