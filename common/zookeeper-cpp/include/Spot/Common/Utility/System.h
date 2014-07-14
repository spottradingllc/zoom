#ifndef SYSTEM_H
#define SYSTEM_H

#include <cstdint>
#include <string>


namespace Spot { namespace Common { namespace Utility
{
  class System
  {
  public:
    static std::string GetHostName();
    static std::string GetProcessId();
    static std::string GetExecutablePath();
    static std::string GetExecutableName( bool shouldStripExtension = false );

    static std::string GetErrorMessage();
    static std::string GetErrorMessage( std::int32_t error );

    static void Immortalize();
  };

} } } // namespaces

#endif
