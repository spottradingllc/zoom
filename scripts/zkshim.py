#!/usr/bin/env python

import logging
import os.path
import sys
import time
from argparse import ArgumentParser
from kazoo.client import KazooClient

ZK_CONN_STRING = ('ZooStaging01:2181, ZooStaging02:2181,'
                  'ZooStaging03:2181, ZooStaging04:2181, ZooStaging05:2181')


class Dependency(object):
    def __init__(self, path):
        self.path = path
        self.done = False

    def reset(self):
        self.done = False


class ZKShim(object):
    def __init__(self, up=None, down=None, timeout=None, gut=None,
                 wait_for_shutdown=False):
        self._zk = KazooClient(hosts=ZK_CONN_STRING)
        self._zk.start()
        self._starttime = 0

        self._upstream = up
        self._downstream = self._create_path_dict(down)
        self._timeout = timeout
        self._gut = gut
        self._wait_for_shutdown = wait_for_shutdown

    @property
    def _all_done(self):
        return all([d.done for d in self._downstream.values()])

    @property
    def _any_done(self):
        return any([d.done for d in self._downstream.values()])

    @property
    def _timed_out(self):
        if self._timeout is None:
            return False
        else:
            return (time.time() - self._starttime) > self._timeout

    def run(self):
        map(self._watch_downstream, self._downstream.values())
        self._delete_existing()

        if self._wait_for_shutdown:
            logging.info('Waiting for running instances to stop')
            while self._any_done:
                time.sleep(2)

        map(lambda x: x.reset(), self._downstream.values())
        map(self._watch_downstream, self._downstream.values())

        self._create_new()
        self._start_timing()

        logging.info('Waiting for watched instances to start.')
        while not self._all_done and not self._timed_out:
            time.sleep(2)

        if self._all_done:
            logging.info('All downstream completed successfully.')
            self._stop()
            sys.exit(0)
        else:
            logging.error('Operation timed out after {0} seconds. '
                          'Exiting with failure.'.format(self._timeout))
            self._stop()
            sys.exit(1)

    def _stop(self):
        self._zk.stop()
        self._zk.close()

    def _start_timing(self):
        self._starttime = time.time()

    def _check_exists(self, path):
        assert self._zk.exists(path), ('Path {0} does not exist in zookeeper. '
                                       'Please input a valid path.'
                                       .format(path))

    def _create_path_dict(self, downlist):
        rdict = dict()
        for path in downlist:
            self._check_exists(path)
            rdict[path] = Dependency(path)
        return rdict

    def _delete_existing(self):
        for p in self._upstream:
            # check exists
            self._check_exists(p)
            children = self._zk.get_children(p)
            for child in [str(c) for c in children]:
                child_path = os.path.join(p, child).replace("\\", "/")
                logging.info('Deleting path {0}'.format(child_path))
                self._zk.delete(child_path)

    def _create_new(self):
        for p in self._upstream:
            new_path = os.path.join(p, 'ZKSHIM').replace("\\", "/")
            logging.info('Creating path {0}'.format(new_path))
            if self._gut is not None:
                self._zk.create(new_path, value=self._gut)
            else:
                self._zk.create(new_path)

    def _watch_downstream(self, event):
        """
        :type event: kazoo.protocol.states.WatchedEvent
        """
        logging.info('Watching path {0}'.format(event.path))
        children = self._zk.get_children(event.path,
                                         watch=self._watch_downstream)
        logging.info(children)
        dep = self._downstream.get(event.path)
        dep.done = bool(children)

    def __str__(self):
        return ('ZKShim(Upstream={0}, Downstream={1}, Timeout={2}, Gut={3})'
                .format(self._upstream, self._downstream.keys(), self._timeout,
                        self._gut))


def get_args():
    parser = ArgumentParser(description='')
    parser.add_argument('-u', '--upstream', nargs='*', default=list(),
                        required=False, metavar='/path/in/zk',
                        help='Input a single or list of zookeeper paths.')
    parser.add_argument('-d', '--downstream', nargs='*', required=True,
                        metavar='/path/in/zk',
                        help='Input a single or list of zookeeper paths.')
    parser.add_argument('-t', '--timeout', type=int, required=False,
                        help='Time in seconds to wait for completion.')
    parser.add_argument('-g', '--gut', type=str, required=False,
                        metavar='HH:MM',
                        help='The gut used by the agent for shutdown time.')
    parser.add_argument('-D', '--dont_wait_for_shutdown', action='store_true',
                        required=False, default=False,
                        help="Whether to wait until a process goes down.")

    return parser.parse_args()


if __name__ == '__main__':
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)-8s | %(message)s'
        )
        logging.getLogger('kazoo.client').setLevel(logging.WARNING)
        args = get_args()
        shim = ZKShim(up=args.upstream, down=args.downstream,
                      timeout=args.timeout, gut=args.gut,
                      wait_for_shutdown=args.dont_wait_for_shutdown)
        logging.info(shim)
        shim.run()
    except AssertionError as ex:
        logging.error('There was an Error during execution:\n{0}'.format(ex))
        sys.exit(1)
