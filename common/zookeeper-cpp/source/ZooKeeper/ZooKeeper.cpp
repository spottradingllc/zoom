#include "Spot/Common/ZooKeeper/ZooKeeper.h"

#include "ZooKeeperImpl.h"


namespace Spot { namespace Common { namespace ZooKeeper
{
  ZooKeeper::ZooKeeper( const std::string& host, int connectionTimeout, int sessionExpirationTimeout, int deterministicConnectionOrder )
  {
    m_zooKeeperImpl = new ZooKeeperImpl( host, connectionTimeout, sessionExpirationTimeout, deterministicConnectionOrder );
  }


  ZooKeeper::~ZooKeeper() noexcept
  {
    if( m_zooKeeperImpl != nullptr )
    {
      delete m_zooKeeperImpl;
    }
  }


  void ZooKeeper::RegisterLogger( Logger::ILogger* logger )
  {
    m_zooKeeperImpl->RegisterLogger( logger );
  }


  void ZooKeeper::UnregisterLogger()
  {
    m_zooKeeperImpl->UnregisterLogger();
  }


  void ZooKeeper::RegisterSessionEventHandler( IZooKeeperSessionEventHandler* eventHandler )
  {
    m_zooKeeperImpl->RegisterSessionEventHandler( eventHandler );
  }


  void ZooKeeper::UnregisterSessionEventHandler()
  {
    m_zooKeeperImpl->UnregisterSessionEventHandler();
  }


  void ZooKeeper::Initialize()
  {
    m_zooKeeperImpl->Initialize();
  }


  void ZooKeeper::Uninitialize()
  {
    m_zooKeeperImpl->Uninitialize();
  }


  const std::string& ZooKeeper::GetHost() const noexcept
  {
    return m_zooKeeperImpl->GetHost();
  }


  int ZooKeeper::GetConnectionTimeout() const noexcept
  {
    return m_zooKeeperImpl->GetConnectionTimeout();
  }


  int ZooKeeper::GetExpirationTimeout() const noexcept
  {
    return m_zooKeeperImpl->GetExpirationTimeout();
  }


  int ZooKeeper::GetDeterministicConnectionOrder() const noexcept
  {
    return m_zooKeeperImpl->GetDeterministicConnectionOrder();
  }


  ZooKeeperStringResult ZooKeeper::GetNode( const std::string& path )
  {
    return m_zooKeeperImpl->GetNode( path );
  }


  ZooKeeperStringResult ZooKeeper::GetNode( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    return m_zooKeeperImpl->GetNode( path, eventHandler );
  }


  ZooKeeperStringVectorResult ZooKeeper::GetNodeChildren( const std::string& path )
  {
    return m_zooKeeperImpl->GetNodeChildren( path );
  }


  ZooKeeperStringVectorResult ZooKeeper::GetNodeChildren( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    return m_zooKeeperImpl->GetNodeChildren( path, eventHandler );
  }


  bool ZooKeeper::CreateNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType )
  {
    return m_zooKeeperImpl->CreateNode( path, data, nodeType );
  }


  std::string ZooKeeper::CreateSequentialNode( const std::string& path, const std::string& data, ZooKeeperNodeType nodeType )
  {
    return m_zooKeeperImpl->CreateSequentialNode( path, data, nodeType );
  }


  void ZooKeeper::ChangeNode( const std::string& path, const std::string& data )
  {
    m_zooKeeperImpl->ChangeNode( path, data );
  }


  void ZooKeeper::DeleteNode( const std::string& path )
  {
    m_zooKeeperImpl->DeleteNode( path );
  }


  void ZooKeeper::AddNodeEventHandler( const std::string& path, IZooKeeperNodeEventHandler* eventHandler )
  {
    return m_zooKeeperImpl->AddNodeEventHandler( path, eventHandler );
  }


  void ZooKeeper::RemoveNodeEventHandler( const std::string& path )
  {
    m_zooKeeperImpl->RemoveNodeEventHandler( path );
  }

} } } // namespaces
