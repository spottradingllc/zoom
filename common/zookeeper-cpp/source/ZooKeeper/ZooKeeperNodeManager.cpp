#include "ZooKeeperNodeManager.h"

#include <string.h>

#include <boost/format.hpp>

#include "Spot/Common/ZooKeeper/IZooKeeperNodeEventHandler.h"

#include "ZooKeeperEvent.h"
#include "ZooKeeperException.h"
#include "ZooKeeperSessionManager.h"



namespace Spot { namespace Common { namespace ZooKeeper
{
  ZooKeeperNodeManager::ZooKeeperNodeManager( ZooKeeperSessionManager* zooKeeperSessionManager ) :
    m_zooKeeperSessionManager( zooKeeperSessionManager )
  {
  }


  ZooKeeperNodeManager::~ZooKeeperNodeManager() noexcept
  {
    Lock lock( m_mutex );

    // clear the cache if clients forget
    m_nodeEventHandlerMap.clear();
  }


  ZooKeeperStringResult ZooKeeperNodeManager::GetNode( const std::string& path )
  {
    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    char data[MAX_DATA_BUFFER];
    int length = MAX_DATA_BUFFER;

    // gets the data associated with a node synchronously
    int result = zoo_wget( m_zooKeeperSessionManager->GetHandle(), path.c_str(), NULL, NULL, data, &length, &stat );
    if( result == ZOK )
    {
      return std::make_pair( std::string( data, length ), true );
    }
    else if( result == ZNONODE )
    {
      return std::make_pair( std::string(), false );
    }

    throw ZooKeeperException( result );
  }


  ZooKeeperStringResult ZooKeeperNodeManager::GetNode( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    // insert into cache before calling wget to avoid race condition
    Insert( path, eventHandler );

    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    char data[MAX_DATA_BUFFER];
    int length = MAX_DATA_BUFFER;

    // gets the data associated with a node synchronously and set a watcher
    int result = zoo_wget( m_zooKeeperSessionManager->GetHandle(), path.c_str(), ZooKeeperEvent::EventHandler, this, data, &length, &stat );
    if( result == ZOK )
    {
      return std::make_pair( std::string( data, length ), true );
    }
    else if( result == ZNONODE )
    {
      // implement wexists?
      return std::make_pair( std::string(), false );
    }

    throw ZooKeeperException( result );
  }


  ZooKeeperStringVectorResult ZooKeeperNodeManager::GetNodeChildren( const std::string& path )
  {
    String_vector stringVector;

    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    // gets the children associated with a node synchronously
    int result = zoo_wget_children2( m_zooKeeperSessionManager->GetHandle(), path.c_str(), NULL, NULL, &stringVector, &stat );
    if( result == ZOK )
    {
      std::vector< std::string > children;

      for( int32_t i = 0; i < stringVector.count; ++i )
      {
        children.push_back( stringVector.data[i] );
      }

      return std::make_pair( children, true );
    }
    else if( result == ZNONODE )
    {
      return std::make_pair( std::vector< std::string >(), false );
    }

    throw ZooKeeperException( result );
  }


  ZooKeeperStringVectorResult ZooKeeperNodeManager::GetNodeChildren( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    // insert into cache before calling wget to avoid race condition
    Insert( path, eventHandler );

    String_vector stringVector;

    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    // gets the children associated with a node synchronously and set a watcher
    int result = zoo_wget_children2( m_zooKeeperSessionManager->GetHandle(), path.c_str(), ZooKeeperEvent::EventHandler, this, &stringVector, &stat );
    if( result == ZOK )
    {
      std::vector< std::string > children;

      for( int32_t i = 0; i < stringVector.count; ++i )
      {
        children.push_back( stringVector.data[i] );
      }

      return std::make_pair( children, true );
    }
    else if( result == ZNONODE )
    {
      return std::make_pair( std::vector< std::string >(), false );
    }

    throw ZooKeeperException( result );
  }


  bool ZooKeeperNodeManager::CreateNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType )
  {
    int flags = (nodeType == ZooKeeperNodeType::EPHEMERAL) ? ZOO_EPHEMERAL : 0;

    // create a persistent or ephemeral node synchronously
    int result = zoo_create( m_zooKeeperSessionManager->GetHandle(), path.c_str(), data.c_str(), data.size(), &ZOO_OPEN_ACL_UNSAFE, flags, NULL, 0 );
    if( result == ZOK )
    {
      return true;
    }
    else if( result == ZNODEEXISTS )
    {
      return false;
    }

    throw ZooKeeperException( result );
  }


  std::string ZooKeeperNodeManager::CreateSequentialNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType )
  {
    int flags = ZOO_SEQUENCE;
    flags |= (nodeType == ZooKeeperNodeType::EPHEMERAL ? ZOO_EPHEMERAL : 0);

    char sequencedPath[MAX_PATH_BUFFER];

    // create a sequential (persistent or ephemeral) node synchronously
    int result = zoo_create( m_zooKeeperSessionManager->GetHandle(), path.c_str(), data.c_str(), data.size(), &ZOO_OPEN_ACL_UNSAFE, flags, sequencedPath, sizeof( sequencedPath ) );
    if( result == ZOK )
    {
      return std::string( sequencedPath, strlen( sequencedPath ) );
    }

    throw ZooKeeperException( result );
  }


  void ZooKeeperNodeManager::ChangeNode( const std::string& path, const std::string& data )
  {
    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    // set the data of a node synchronously
    int result = zoo_set2( m_zooKeeperSessionManager->GetHandle(), path.c_str(), data.c_str(), data.size(), -1, &stat );
    if( result != ZOK )
    {
      throw ZooKeeperException( result );
    }
  }


  void ZooKeeperNodeManager::DeleteNode( const std::string& path )
  {
    // delete a node synchronously
    int result = zoo_delete( m_zooKeeperSessionManager->GetHandle(), path.c_str(), -1 );
    if( result != ZOK )
    {
      throw ZooKeeperException( result );
    }
  }


  void ZooKeeperNodeManager::AddEventHandler( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    Insert( path, eventHandler );

    Stat stat;
    memset( &stat, 0, sizeof( stat ) );

    int result = zoo_wexists( m_zooKeeperSessionManager->GetHandle(), path.c_str(), ZooKeeperEvent::EventHandler, this, &stat );
    if( (result != ZOK) && (result != ZNONODE) )
    {
      throw ZooKeeperException( result );
    }
  }


  void ZooKeeperNodeManager::RemoveEventHandler( const std::string& path )
  {
    bool result = Erase( path );
    if( !result )
    {
      throw std::runtime_error( boost::str( boost::format( "Node <%s> event handler does not exist" ) % path ) );
    }
  }


  void ZooKeeperNodeManager::FireEvent( zhandle_t* zhandle, int type, int state, const char* path )
  {
    unused( zhandle, state );

    Lock lock( m_mutex );

    auto it = m_nodeEventHandlerMap.find( path );
    if( it != m_nodeEventHandlerMap.end() )
    {
      if( type == ZOO_CREATED_EVENT )
      {
        it->second->OnNodeCreated( it->first );
      }
      else if( type == ZOO_CHANGED_EVENT )
      {
        it->second->OnNodeChanged( it->first );
      }
      else if( type == ZOO_CHILD_EVENT )
      {
        it->second->OnNodeChildrenChanged( it->first );
      }
      else if( type == ZOO_DELETED_EVENT )
      {
        it->second->OnNodeDeleted( it->first );
      }
      else if( type == ZOO_NOTWATCHING_EVENT )
      {
      }
    }
  }


  bool ZooKeeperNodeManager::Insert( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    Lock lock( m_mutex );

    auto result = m_nodeEventHandlerMap.insert( std::make_pair( path, eventHandler ) );

    return result.second;
  }


  bool ZooKeeperNodeManager::Erase( const std::string& path )
  {
    bool result = false;

    Lock lock( m_mutex );

    auto it = m_nodeEventHandlerMap.find( path );
    if( it != m_nodeEventHandlerMap.end() )
    {
      m_nodeEventHandlerMap.erase( it );

      result = true;
    }

    return result;
  }

} } } // namespaces
