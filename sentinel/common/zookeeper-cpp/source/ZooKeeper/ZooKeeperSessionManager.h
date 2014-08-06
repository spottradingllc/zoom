#ifndef ZOO_KEEPER_SESSION_MANAGER_H
#define ZOO_KEEPER_SESSION_MANAGER_H

#include <condition_variable>
#include <mutex>
#include <string>

#include <zookeeper/zookeeper.h>


namespace Spot { namespace Common { namespace ZooKeeper
{
  class IZooKeeperSessionEventHandler;

  class ZooKeeperSessionManager
  {
  public:  
    ZooKeeperSessionManager( const std::string& host, int connectionTimeout, int expirationTimeout, int deterministicConnectionOrder );
    ~ZooKeeperSessionManager() noexcept;

    void Initialize();
    void Uninitialize();

    void RegisterEventHandler( IZooKeeperSessionEventHandler* eventHandler );
    void UnregisterEventHandler();

    zhandle_t* GetHandle() const noexcept;

    const std::string& GetHost() const noexcept;
    int GetConnectionTimeout() const noexcept;
    int GetExpirationTimeout() const noexcept;
    int GetDeterministicConnectionOrder() const noexcept;

    void FireEvent( zhandle_t* zhandle, int state );

  private:
    std::string m_host;
    int m_connectionTimeout;
    int m_expirationTimeout;
    int m_deterministicConnectionOrder;

    zhandle_t* m_handle;
    bool m_isInitialized;

    typedef std::unique_lock< std::mutex > Lock;
    std::mutex m_sessionMutex;
    std::mutex m_clientMutex;

    std::condition_variable m_condition;

    IZooKeeperSessionEventHandler* m_eventHandler;
  };

} } } // namespaces

#endif
