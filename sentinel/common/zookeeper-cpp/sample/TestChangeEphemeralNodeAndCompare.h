#ifndef TEST_CHANGE_EPHEMERAL_NODE_AND_COMPARE_H
#define TEST_CHANGE_EPHEMERAL_NODE_AND_COMPARE_H

#include <condition_variable>
#include <mutex>

#include "Spot/Common/Logger/ILogger.h"
#include "Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"
#include "Spot/Common/ZooKeeper/ZooKeeper.h"

#include "ITest.h"


namespace Spot
{
  class TestChangeEphemeralNodeAndCompare final : public ITest, public ZooKeeper::IZooKeeperSessionEventHandler
  {
  public:
    TestChangeEphemeralNodeAndCompare( Logger::ILogger* logger, ZooKeeper::ZooKeeper* zooKeeper );
    virtual ~TestChangeEphemeralNodeAndCompare() noexcept;

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
  };
}

#endif
