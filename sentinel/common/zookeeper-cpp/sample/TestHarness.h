#ifndef TEST_HARNESS_H
#define TEST_HARNESS_H

#include <memory>
#include <string>
#include <vector>

#include "Spot/Common/Logger/ILogger.h"
#include "Spot/Common/ZooKeeper/ZooKeeper.h"

#include "ITest.h"

using namespace Spot::Common;


namespace Spot
{
  class TestHarness
  {
  public:
    TestHarness( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder );
    ~TestHarness() noexcept;

    void Run();

  private:
    Logger::ILogger* m_logger;
    ZooKeeper::ZooKeeper* m_zooKeeper;

    typedef std::shared_ptr< ITest > ITestPtr;

    typedef std::vector< ITestPtr > Tests;
    Tests m_tests;
  };

} // namespace

#endif
