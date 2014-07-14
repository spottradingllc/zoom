#ifndef ILOGGER_H
#define ILOGGER_H

#include <string>


namespace Spot { namespace Common { namespace Logger
{
  enum class Level { OFF = __INT_MAX__, FATAL = 50000, ERROR = 40000, WARN = 30000, INFO = 20000, DEBUG = 10000, TRACE = 5000, ALL = (-__INT_MAX__ - 1) };

  class ILogger
  {
  public:
    virtual ~ILogger() noexcept {}

    virtual void Initialize( const std::string& node ) = 0;
    virtual void Uninitialize() = 0;

    virtual Level GetLevel() const noexcept = 0;

    virtual void Write( Level level, const std::string& message, const char* const fileName, const char* const functionName, int lineNumber ) = 0;
  };


  #define LOGGER_FATAL( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::FATAL )\
      logger->Write( Spot::Common::Logger::Level::FATAL, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }


  #define LOGGER_ERROR( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::ERROR )\
      logger->Write( Spot::Common::Logger::Level::ERROR, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }


  #define LOGGER_WARN( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::WARN )\
      logger->Write( Spot::Common::Logger::Level::WARN, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }


  #define LOGGER_INFO( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::INFO )\
      logger->Write( Spot::Common::Logger::Level::INFO, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }


  #define LOGGER_DEBUG( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::DEBUG )\
      logger->Write( Spot::Common::Logger::Level::DEBUG, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }


  #define LOGGER_TRACE( logger, message )\
  {\
    if( logger->GetLevel() <= Spot::Common::Logger::Level::TRACE )\
      logger->Write( Spot::Common::Logger::Level::TRACE, message, __FILE__, __PRETTY_FUNCTION__, __LINE__ );\
  }

} } } // namespaces

#endif
