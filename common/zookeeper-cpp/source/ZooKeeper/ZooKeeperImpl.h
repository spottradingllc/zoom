#ifndef ZOO_KEEPER_IMPL_H
#define ZOO_KEEPER_IMPL_H

#include <memory>
#include <string>

#include "Spot/Common/Logger/ILogger.h"
#include "Spot/Common/ZooKeeper/IZooKeeperNodeEventHandler.h"
#include "Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"
#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"

#include "ZooKeeperNodeManager.h"
#include "ZooKeeperSessionManager.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  class ZooKeeperNodeManager;
  class IZooKeeperNodeEventHandler;

  class ZooKeeperImpl
  {
  public:
    ZooKeeperImpl( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder );
    ~ZooKeeperImpl() noexcept;

    void RegisterLogger( Logger::ILogger* logger );
    void UnregisterLogger();

    void RegisterSessionEventHandler( IZooKeeperSessionEventHandler* eventHandler );
    void UnregisterSessionEventHandler();

    void Initialize();
    void Uninitialize();

    const std::string& GetHost() const noexcept;
    int GetConnectionTimeout() const noexcept;
    int GetExpirationTimeout() const noexcept;
    int GetDeterministicConnectionOrder() const noexcept;

    ZooKeeperStringResult GetNode( const std::string& path );
    ZooKeeperStringResult GetNode( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );

    ZooKeeperStringVectorResult GetNodeChildren( const std::string& path );
    ZooKeeperStringVectorResult GetNodeChildren( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );

    bool CreateNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType );
    std::string CreateSequentialNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType );
    void ChangeNode( const std::string& path, const std::string& data );
    void DeleteNode( const std::string& path );

    void AddNodeEventHandler( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );
    void RemoveNodeEventHandler( const std::string& path );

  private:
    static const int MAX_PATH_BUFFER = 1024;
    static const int MAX_DATA_BUFFER = 1024 * 1024;

    Logger::ILogger* m_logger;

    ZooKeeperNodeManager* m_zooKeeperNodeManager;
    ZooKeeperSessionManager* m_zooKeeperSessionManager;
  };

} } } // namespaces

#endif
