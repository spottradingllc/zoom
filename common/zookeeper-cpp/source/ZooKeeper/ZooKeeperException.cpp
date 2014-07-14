#include "ZooKeeperException.h"

#include <errno.h>

#include <zookeeper/zookeeper.h>

#include <boost/format.hpp>


namespace Spot { namespace Common { namespace ZooKeeper
{
  ZooKeeperException::ZooKeeperException( int error )
  {
    const char* description = zerror( error );

    if( error == ZSYSTEMERROR )
    {
      m_what = boost::str( boost::format( "Error <%d> Description <%s> errno:%d" ) % error % description % errno );
    }
    else
    {
      m_what = boost::str( boost::format( "Error <%d> Description <%s>" ) % error % description );
    }
  }


  ZooKeeperException::ZooKeeperException( int error, const std::string& description )
  {
    m_what = boost::str( boost::format( "Error <%d> Description <%s>" ) % error % description );
  }


  ZooKeeperException::~ZooKeeperException() noexcept
  {
  }


  const char* ZooKeeperException::what() const noexcept
  {
    return m_what.c_str();
  }

} } } // namespaces
