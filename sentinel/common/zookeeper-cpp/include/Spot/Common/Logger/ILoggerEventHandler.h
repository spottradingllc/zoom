#ifndef ILOG_EVENT_HANDLER_H
#define ILOG_EVENT_HANDLER_H

#include <string>


namespace Spot { namespace Common { namespace Logger
{
  class ILoggerEventHandler
  {
  public:
    virtual ~ILoggerEventHandler() noexcept {}

    virtual void OnWrite( Spot::Common::Logger::Level level, const std::string& message ) = 0;
  };

} } } // namespaces

#endif
