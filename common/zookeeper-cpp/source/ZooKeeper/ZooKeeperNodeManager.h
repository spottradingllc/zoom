#ifndef ZOO_KEEPER_NODE_MANAGER_H
#define ZOO_KEEPER_NODE_MANAGER_H

#include <memory>
#include <map>
#include <mutex>
#include <string>

#include <zookeeper/zookeeper.h>

#include "Spot/Common/ZooKeeper/ZooKeeperFwd.h"
#include "Spot/Common/ZooKeeper/ZooKeeperTypes.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  class IZooKeeperNodeEventHandler;
  class ZooKeeperSessionManager;

  class ZooKeeperNodeManager
  {
  public:
    ZooKeeperNodeManager( ZooKeeperSessionManager* zooKeeperSessionManager );
    ~ZooKeeperNodeManager() noexcept;

    ZooKeeperStringResult GetNode( const std::string& path );
    ZooKeeperStringResult GetNode( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );

    ZooKeeperStringVectorResult GetNodeChildren( const std::string& path );
    ZooKeeperStringVectorResult GetNodeChildren( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );

    bool CreateNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType );
    std::string CreateSequentialNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType );
    void ChangeNode( const std::string& path, const std::string& data );
    void DeleteNode( const std::string& path );

    void AddEventHandler( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );
    void RemoveEventHandler( const std::string& path );

    void FireEvent( zhandle_t* zhandle, int type, int state, const char* path );

  private:
    static const int MAX_PATH_BUFFER = 1024;
    static const int MAX_DATA_BUFFER = 1024 * 1024;

    ZooKeeperSessionManager* m_zooKeeperSessionManager;

    typedef std::lock_guard< std::mutex > Lock;
    std::mutex m_mutex;

    typedef std::map< std::string, IZooKeeperNodeEventHandler* > NodeEventHandlerMap;
    NodeEventHandlerMap m_nodeEventHandlerMap;

    // helper function(s)
    bool Insert( const std::string& path, IZooKeeperNodeEventHandler* eventHandler );
    bool Erase( const std::string& path );
  };

} } } // namespaces

#endif
