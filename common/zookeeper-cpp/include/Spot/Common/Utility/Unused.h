#ifndef UNUSED_H
#define UNUSED_H

namespace
{
  template< class... T >
  void unused( T&&... )
  {
  }
}

#endif
