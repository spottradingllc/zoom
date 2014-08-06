#include "Spot/Common/Utility/System.h"

#include <sstream>
#include <stdexcept>

#include <errno.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>


namespace
{
  static const size_t MAX_HOST_NAME = 255;
  static const size_t MAX_PATH = 1024;
}


namespace Spot { namespace Common { namespace Utility
{
  std::string System::GetHostName()
  {
    char name[MAX_HOST_NAME + 1];

    int result = gethostname( name, sizeof( name ) );
    if( result != 0 )
    {
      throw std::runtime_error( GetErrorMessage( result ) );
    }

    return name;
  }


  std::string System::GetProcessId()
  {
    pid_t pid = getpid();

    std::ostringstream result;
    result << pid;

    return result.str();
  }


  std::string System::GetExecutablePath()
  {
    std::ostringstream temp;
    temp << "/proc/" << getpid() << "/exe" << std::ends;

    char path[MAX_PATH + 2];

    ssize_t linksize = readlink( temp.str().c_str(), path, (sizeof( path ) - 1) );
    if( linksize == -1 )
    {
      throw std::runtime_error( GetErrorMessage().c_str() );
    }

    path[linksize] = '\0';

    // strip executable name
    char* buffer = ::strrchr( path, '/' );
    if( buffer != NULL )
    {
      *buffer = '\0';
    }

    return path;
  }


  std::string System::GetExecutableName( bool shouldStripExtension )
  {
    std::ostringstream temp;
    temp << "/proc/" << getpid() << "/exe" << std::ends;

    char execPath[MAX_PATH + 2];
    ssize_t linksize = readlink(temp.str().c_str(), execPath, sizeof(execPath) -1);

    if( linksize == -1 )
    {
      throw std::runtime_error( GetErrorMessage().c_str() );
    }

    execPath[linksize] = '\0';
    std::string path( execPath );

    // include everything from the last slash to the end of the string
    size_t index = path.rfind( '/' );
    if( index != std::string::npos )
    {
      path = path.substr( index + 1 );
    }

    if( shouldStripExtension )
    {
      size_t index = path.find( '.' );
      if( index != std::string::npos )
      {
        path = path.substr( 0, index );
      }
    }

    return path;
  }


  std::string System::GetErrorMessage()
  {
    return GetErrorMessage( errno );
  }


  std::string System::GetErrorMessage( std::int32_t error )
  {
    char buffer[1024];
    strerror_r( error, buffer, sizeof( buffer ) );

    return buffer;
  }


  void System::Immortalize()
  {
    // Step 1: Fork to run in background. Parent terminates and returns control to shell from whence it came.
    pid_t pid = fork();
    if( pid != 0 )
    {
      exit( 0 );
    }

    // Step 2: Start a new session and automatically become the session leader
    setsid();

    // Step 3: Fork again so we are no longer the session leader;
    //         This prevents this process from accidentally acquiring a terminal.
    //         Terminating the session leader (parent) generates SIGHUP, which we ignore.
    // Handled by caller: signal( SIGHUP, SIG_IGN );

    pid = fork();
    if( pid != 0 )
    {
      exit( 0 );
    }

    // Step 4: Be sure our working directory will not be modified or removed.
    chdir( "/" );

    // Step 5: Forget any inherited file creation mask bits
    umask( 0 );

    // Step 6: Try to close file handles.
    //         We don't want any handles pointing to the tty.
    //         Alas we don't know how many FD's might be in use, so we guess.
    static unsigned int MAX_FD = 256;

    for( unsigned int fd = 0; fd < MAX_FD; ++fd )
    {
      close( fd );
    }
  }

} } } // namespaces
