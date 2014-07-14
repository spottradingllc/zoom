#include "Spot/Common/Logger/Log4cxxLogger.h"

#include <log4cxx/helpers/transcoder.h>
#include <log4cxx/xml/domconfigurator.h>


namespace Spot { namespace Common { namespace Logger
{
  Log4cxxLogger::Log4cxxLogger() : m_level( Level::OFF )
  {
  }


  Log4cxxLogger::~Log4cxxLogger() noexcept
  {
  }


  void Log4cxxLogger::Initialize( const std::string& configurationFile  )
  {
    log4cxx::xml::DOMConfigurator::configure( configurationFile );

    m_logger = log4cxx::Logger::getRootLogger();

    int level = m_logger->getLevel()->toInt();
    switch( level )
    {
      case log4cxx::Level::FATAL_INT:
        m_level = Level::FATAL;
        break;

      case log4cxx::Level::ERROR_INT:
        m_level = Level::ERROR;
        break;

      case log4cxx::Level::WARN_INT:
        m_level = Level::WARN;
        break;

      case log4cxx::Level::INFO_INT:
        m_level = Level::INFO;
        break;

      case log4cxx::Level::DEBUG_INT:
        m_level = Level::DEBUG;
        break;

      case log4cxx::Level::TRACE_INT:
        m_level = Level::TRACE;
        break;

      case log4cxx::Level::ALL_INT:
        m_level = Level::ALL;
        break;
    }
  }


  void Log4cxxLogger::Uninitialize()
  {
  }


  Level Log4cxxLogger::GetLevel() const noexcept
  {
    return m_level;
  }


  void Log4cxxLogger::Write( Level level, const std::string& message, const char* const fileName, const char* const functionName, int lineNumber )
  {
    log4cxx::spi::LocationInfo locationInfo( fileName, functionName, lineNumber );

    switch( level )
    {
      case Level::OFF:
        break;

      case Level::FATAL:
        m_logger->fatal( message, locationInfo );
        break;

      case Level::ERROR:
        m_logger->error( message, locationInfo );
        break;

      case Level::WARN:
        m_logger->warn( message, locationInfo );
        break;

      case Level::INFO:
        m_logger->info( message, locationInfo );
        break;

      case Level::DEBUG:
        m_logger->debug( message, locationInfo );
        break;

      case Level::TRACE:
        m_logger->trace( message, locationInfo );
        break;

      case Level::ALL:
        break;
    }
  }

} } } // namespaces
