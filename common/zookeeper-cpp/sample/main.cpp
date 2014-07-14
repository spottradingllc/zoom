#include <signal.h>
#include <unistd.h>

#include <iostream>

#include <boost/format.hpp>
#include <boost/program_options.hpp>

#include "TestHarness.h"

using namespace Spot;


void SignalHandler( int signo )
{
  if( signo == SIGINT )
  {
    std::cout << "SIGINT caught" << std::endl;
  }
}


int main( int argc, char** argv )
{
  try
  {
    if( signal( SIGINT, SignalHandler ) == SIG_ERR ) // 2
    {
      std::cout << "Cannot catch SIGINT" << std::endl;
    }

    std::string host;
    int connectionTimeout;
    int sessionExpirationTimeout;
    int deterministicConnectionOrder;
    int test;

    boost::program_options::options_description options( "Allowed options" );
    options.add_options()
      ( "help,h", "Help message" )
      ( "host", boost::program_options::value< std::string >( &host )->default_value( "zoostaging01:2181,zoostaging02:2181,zoostaging03:2181,zoostaging04:2181,zoostaging05:2181" ), "Host" )
      ( "connection-timeout", boost::program_options::value< int >( &connectionTimeout )->default_value( 5 ), "Connection timeout in seconds" )
      ( "session-expiration-timeout", boost::program_options::value< int >( &sessionExpirationTimeout )->default_value( 15 ), "Session expiration timeout in seconds" )
      ( "deterministic-connection-order", boost::program_options::value< int >( &deterministicConnectionOrder )->default_value( 0 ), "0 - no, 1 - yes (use 1 for testing)" )
      ( "test", boost::program_options::value< int >( &test )->default_value( 1 ), "Test case" );

    boost::program_options::variables_map commandLineMap;
    boost::program_options::store( boost::program_options::parse_command_line( argc, argv, options ), commandLineMap );
    boost::program_options::notify( commandLineMap );

    if( commandLineMap.count( "help" ) )
    {
      std::cout << options << "\n";
    }
    else
    {
      TestHarness testHarness( host, connectionTimeout, sessionExpirationTimeout, deterministicConnectionOrder );
      testHarness.Run();
    }
  }
  catch( const std::exception& ex )
  {
    std::cout << ex.what() << std::endl;
  }

  return 0;
}
