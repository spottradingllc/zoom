#ifndef IAPPLICATION_EVENT_HANDLER_H
#define IAPPLICATION_EVENT_HANDLER_H


namespace Spot { namespace Common { namespace Application
{
  class IApplicationEventHandler
  {
  public:
    virtual ~IApplicationEventHandler() noexcept {}

    virtual void OnInitialize() = 0;
    virtual void OnStart() = 0;
    virtual void OnStop() = 0;
    virtual void OnUninitialize() = 0;
  };

} } } // namespaces

#endif
