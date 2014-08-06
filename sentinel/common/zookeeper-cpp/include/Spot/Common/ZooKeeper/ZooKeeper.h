#ifndef ZOO_KEEPER_H
#define ZOO_KEEPER_H

#include <string>

#include "Spot/Common/Logger/ILogger.h"

#include "Spot/Common/ZooKeeper/IZooKeeperNodeEventHandler.h"
#include "Spot/Common/ZooKeeper/IZooKeeperSessionEventHandler.h"

#include "ZooKeeperFwd.h"
#include "ZooKeeperTypes.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  class ZooKeeperImpl;

  class ZooKeeper
  {
  public:  
    ZooKeeper( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder );
    ~ZooKeeper() noexcept;

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

    bool CreateNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType = ZooKeeperNodeType::PERSISTENT );
    std::string CreateSequentialNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType = ZooKeeperNodeType::PERSISTENT );
    void ChangeNode( const std::string& path, const std::string& data );
    void DeleteNode( const std::string& path );

    void AddNodeEventHandler( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );
    void RemoveNodeEventHandler( const std::string& path );

  private:
    ZooKeeperImpl* m_zooKeeperImpl;
  };

} } } // namespaces

#endif
