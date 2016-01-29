""" Integration test: refuse call
"""
import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import logging

from nose.tools import *
import nose
import inte_testutils
from telewall.core.model import TelephoneNumber
from telewall.core.util import sleep_until

logging.basicConfig(level=logging.WARN)
LOG = logging.getLogger('telewall')
LOG.setLevel(logging.DEBUG)


def test_Anruf_blockieren():
    u = inte_testutils.TestUtil()
    u.block_callerid(TelephoneNumber('0790000002'))

    call = u.make_call_to_incoming(callerid='0790000002')

    sleep_until(lambda: 'Ringing' in call.get_call_states() or 'Up' in call.get_call_states(), 5)
    call.hangup()

    states = call.get_call_states()
    assert_false('Ringing' in states,
                 'Das analoge Telefon sollte NICHT angerufen werden, aber es gab einen "Ringing" Status.')
    call.stop()


if __name__ == '__main__':
    nose.runmodule()
