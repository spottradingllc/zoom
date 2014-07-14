#include "ZooKeeperStat.h"

#include <boost/format.hpp>


namespace Spot { namespace Common { namespace ZooKeeper
{
  ZooKeeperStat::ZooKeeperStat( const Stat& stat ) : m_stat( stat )
  {
  }


  ZooKeeperStat::~ZooKeeperStat() noexcept
  {
  }


  int32_t ZooKeeperStat::GetAversion() const noexcept
  {
    return m_stat.aversion;
  }


  int64_t ZooKeeperStat::GetCtime() const noexcept
  {
    return m_stat.ctime;
  }


  int32_t ZooKeeperStat::GetCversion() const noexcept
  {
    return m_stat.cversion;
  }


  int64_t ZooKeeperStat::GetCzxid() const noexcept
  {
    return m_stat.czxid;
  }


  int32_t ZooKeeperStat::GetDataLength() const noexcept
  {
    return m_stat.dataLength;
  }


  int64_t ZooKeeperStat::GetEphemeralOwner() const noexcept
  {
    return m_stat.ephemeralOwner;
  }


  int64_t ZooKeeperStat::GetMtime() const noexcept
  {
    return m_stat.mtime;
  }


  int64_t ZooKeeperStat::GetMzxid() const noexcept
  {
    return m_stat.mzxid;
  }


  int32_t ZooKeeperStat::GetNumChildren() const noexcept
  {
    return m_stat.numChildren;
  }


  int64_t ZooKeeperStat::GetPzxid() const noexcept
  {
    return m_stat.pzxid;
  }


  int32_t ZooKeeperStat::GetVersion() const noexcept
  {
    return m_stat.version;
  }


  std::ostream& operator<<( std::ostream& out, const ZooKeeperStat& zooKeeperStat )
  {
    boost::format result( "aversion <%d> ctime <%ld> cversion <%d> czxid <%ld> dataLength <%d> ephemeralOwner <%ld> mtime <%ld> mzxid <%ld> numChildren <%d> pzxid <%ld> version <%d>" );
    result % zooKeeperStat.m_stat.aversion;
    result % zooKeeperStat.m_stat.ctime;
    result % zooKeeperStat.m_stat.cversion;
    result % zooKeeperStat.m_stat.czxid;
    result % zooKeeperStat.m_stat.dataLength;
    result % zooKeeperStat.m_stat.ephemeralOwner;
    result % zooKeeperStat.m_stat.mtime;
    result % zooKeeperStat.m_stat.mzxid;
    result % zooKeeperStat.m_stat.numChildren;
    result % zooKeeperStat.m_stat.pzxid;
    result % zooKeeperStat.m_stat.version;


    return out << result.str();
  }

} } } // namespaces
