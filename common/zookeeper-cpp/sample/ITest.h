#ifndef ITEST_H
#define ITEST_H

#include "Spot/Common/Application/IApplicationEventHandler.h"

using namespace Spot::Common;


namespace Spot
{
  class ITest
  {
  public:
    virtual ~ITest() noexcept {}

    virtual void StartUp() = 0;
    virtual void Execute() = 0;
    virtual void TearDown() = 0;
  };

} // namespace

#endif
