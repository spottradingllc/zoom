#ifndef ZOO_KEEPER_EXCEPTION_H
#define ZOO_KEEPER_EXCEPTION_H

#include <exception>
#include <string>


namespace Spot { namespace Common { namespace ZooKeeper
{
  class ZooKeeperException final : public std::exception
  {
  public:
    explicit ZooKeeperException( int error );
    explicit ZooKeeperException( int error, const std::string& description );
    virtual ~ZooKeeperException() noexcept override;

    virtual const char* what() const noexcept override;

  private:
    std::string m_what;
  };

} } } // namespaces

#endif
