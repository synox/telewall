"""
This Application handles incomming calls, shows status using led and the display, and reacts to button presses.

This file just starts the required components. They are run in their own thread.

This must run on python2.7 because the ari package currently does not support python3.
(https://github.com/asterisk/ari-py/issues/17)
"""

from __future__ import print_function

import logging
import signal
import sys
import time

from telewall.ui import ui
from telewall.asterisk import app_block_call
from telewall.asterisk import app_incoming_call
from telewall.asterisk import app_manage_recording_call
from telewall.asterisk import app_unblock_call
from telewall.core.config import Config

LOG = logging.getLogger(__name__)


def handle_signal(signum=None, frame=None):
    """ The SIGTERM signal tells the application it should quit. When that signal is received, app the threads
    should be stopped.
    """
    try:
        terminate()
    except:
        pass
    print('Goodbye')
    sys.exit(0)


def start():
    """
    start the sub-applications
    """
    logging.basicConfig(filename='/var/log/telewall-app.log', level=logging.WARN)
    logging.getLogger('telewall').setLevel(logging.DEBUG)

    LOG.info('using config %s', Config)

    # each ui component has its own thread
    ui.start()

    # asterisk apps run in their own thread
    app_manage_recording_call.start()
    app_incoming_call.start()
    app_block_call.start()
    app_unblock_call.start()


def terminate():
    """ stop all applications (due to shutdown)
    """
    ui.stop()

    app_manage_recording_call.stop()
    app_incoming_call.stop()
    app_block_call.stop()
    app_unblock_call.stop()


if __name__ == '__main__':

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    start()
    while True:
        time.sleep(10)
