#ifndef ZOO_KEEPER_STAT_H
#define ZOO_KEEPER_STAT_H

#include <iostream>
#include <fstream>
#include <sstream>

#include <zookeeper/zookeeper.h>


namespace Spot { namespace Common { namespace ZooKeeper
{
  class ZooKeeperStat
  {
  public:
    ZooKeeperStat( const Stat& stat );
    ~ZooKeeperStat() noexcept;

    int32_t GetAversion() const noexcept;
    int64_t GetCtime() const noexcept;
    int32_t GetCversion() const noexcept;
    int64_t GetCzxid() const noexcept;
    int32_t GetDataLength() const noexcept;
    int64_t GetEphemeralOwner() const noexcept;
    int64_t GetMtime() const noexcept;
    int64_t GetMzxid() const noexcept;
    int32_t GetNumChildren() const noexcept;
    int64_t GetPzxid() const noexcept;
    int32_t GetVersion() const noexcept;

    friend std::ostream& operator<<( std::ostream& out, const ZooKeeperStat& zooKeeperStat );

  private:
    Stat m_stat;
  };

} } } // namespaces

#endif
