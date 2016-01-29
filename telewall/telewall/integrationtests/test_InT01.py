""" Integration test: permit call
"""
import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')


import logging

import nose
from nose.tools import *


import inte_testutils
from telewall.core.model import TelephoneNumber
from telewall.core.util import sleep_until

logging.basicConfig(filename='/tmp/telewall-inte.log', level=logging.DEBUG)
logging.getLogger('telewall').setLevel(logging.DEBUG)

LOG = logging.getLogger(__name__)


def test_Anruf_erlauben():
    u = inte_testutils.TestUtil()
    u.unblock_callerid(TelephoneNumber('0790000001'))

    call = u.make_call_to_incoming(callerid='0790000001')
    LOG.info('call: %s', call)
    sleep_until(lambda: 'Ringing' in call.get_call_states() or 'Up' in call.get_call_states(), 5)
    call.hangup()

    states = call.get_call_states()
    LOG.info('states: %s', states)
    assert_true('Ringing' in states,
                'Das analoge Telefon sollte angerufen worden sein, aber es gab keinen "Ringing" Status.')
    call.stop()


if __name__ == '__main__':
    nose.runmodule()
