#ifndef LOG4CXX_LOGGER_H
#define LOG4CXX_LOGGER_H

#include <string>

#include <log4cxx/logger.h>

#include "ILogger.h"


namespace Spot { namespace Common { namespace Logger
{
  class Log4cxxLogger final : public ILogger
  {
  public:
    Log4cxxLogger();
    virtual ~Log4cxxLogger() noexcept override;

    void Initialize( const std::string& configurationFile ) override;
    void Uninitialize() override;

    virtual Level GetLevel() const noexcept override;

    virtual void Write( Level level, const std::string& message, const char* const fileName, const char* const functionName, int lineNumber ) override final;

  private:
    log4cxx::LoggerPtr m_logger;

    Level m_level;
  };

} } } // namespaces

#endif
