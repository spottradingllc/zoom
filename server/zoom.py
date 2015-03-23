import logging
import platform
import traceback

from argparse import ArgumentParser
from zoom.www.entities.session import Session


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('-p', '--port', type=int,
                    help='Which port the server should listen on. ')
    ap.add_argument('-e', '--environment',
                    help='The environment to connect to. '
                         'This is an over-ride for the setting in the config')
    return ap.parse_args()


if __name__ == "__main__":
    try:
        if 'Linux' in platform.platform():
            from setproctitle import setproctitle
            logging.info('Changing the process name to Zoom')
            setproctitle('Zoom')  # Changes process name

        settings = vars(parse_args())
        session = Session(**settings)
        session.start()

        session.stop()

    except Exception as e:
        print traceback.format_exc()
        print str(e)
