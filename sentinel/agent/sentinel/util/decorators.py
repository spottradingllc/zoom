import logging
import time
import traceback
from functools import wraps
from kazoo.exceptions import ConnectionLoss


def connected(method):
    """
    Decorator for ensuring zookeeper client is connected.
    """
    @wraps(method)
    def connected_wrapper(cls, *args, **kwargs):
        _log = logging.getLogger('decorator.connected')
        if hasattr(cls, 'zkclient'):
            if cls.zkclient.connected:
                try:
                    return method(cls, *args, **kwargs)
                except ConnectionLoss:
                    _log.warning('ZK client lost connection during {0}'
                                 .format(method.__name__))
            else:
                _log.warning('ZK client disconnected. Cannot run {0}'
                             .format(method.__name__))

    return connected_wrapper


def catch_exception(*ex, **ex_kwargs):
    """
    Decorator to catch, log, and pass Exceptions
    :type ex: one or more Exceptions
    :type ex_kwargs: dict
        {msg: str, 'traceback': bool}
    """
    def wrap(method):
        @wraps(method)
        def catch_wrapper(cls, *args, **kwargs):
            _log = logging.getLogger('decorator.ex')
            try:
                return method(cls, *args, **kwargs)
            except ex as exception:
                msg = ex_kwargs.get('msg', None)
                if msg is not None:
                    _log.warning(msg)
                else:
                    _log.warning('{0} caught for {1}.{2} with args {3} '
                                 'and kwargs {4}'.format(type(exception),
                                                         cls,
                                                         method.__name__,
                                                         args, kwargs))
                tb = ex_kwargs.get('traceback', None)
                if tb:
                    _log.warning(traceback.format_exc())

        return catch_wrapper
    return wrap


def time_this(method):
    @wraps(method)
    def time_this_wrapper(cls, *args, **kwargs):
        _log = logging.getLogger('decorator.time')
        start_time = time.time()
        result = method(cls, *args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time

        _log.info('%r: %2.2f sec' % (method.__name__,  duration))
        return result

    return time_this_wrapper


def synchronous(lockname):
    """
    A decorator to place an instance-based lock around a method.
    By convention, the attribute names should be the same for shared locks.
    Based on:
    http://code.activestate.com/recipes/577105-synchronization-decorator-for-class-methods
    :param lockname: The attribute representing the Lock object
    :type lockname: str
    """
    def _synched(method):
        @wraps(method)
        def _synchronizer(cls, *args, **kwargs):
            _log = logging.getLogger('decorator.lock')
            lock = cls.__getattribute__(lockname)
            _log.debug('Waiting for lock id "{0}" for method "{1}"'
                       .format(lockname, method.__name__))
            lock.acquire()
            _log.debug('Locked. Running action "{0}"'.format(method.__name__))
            try:
                return method(cls, *args, **kwargs)
            finally:
                lock.release()
        return _synchronizer
    return _synched

def run_only_one(lockname):
    """
    A decorator to place an instance-based lock around a method.
    If the lock has been acquired however, the instance that couldn't acquire
    the lock will return without running the method.
    By convention, the attribute names should be the same for shared locks.
    Based on:
    http://code.activestate.com/recipes/577105-synchronization-decorator-for-class-methods
    :param lockname: The attribute representing the Lock object
    :type lockname: str
    """
    def _synched(method):
        @wraps(method)
        def _synchronizer(cls, *args, **kwargs):
            _log = logging.getLogger('one.lock')
            lock = cls.__getattribute__(lockname)
            _log.debug('Waiting for lock id "{0}" for method "{1}"'
                       .format(lockname, method.__name__))
            if lock.acquire(False):
                _log.debug('Locked. Running action "{0}"'.format(method.__name__))
                try:
                    return method(cls, *args, **kwargs)
                finally:
                    lock.release()
                    _log.debug('Single lock released')
            else:
                _log.debug('Lock not available. Not running method "{0}"'.format(method.__name__))
                return 0
        return _synchronizer
    return _synched
