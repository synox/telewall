import os
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import nose
import logging
import requests
import inte_testutils
from nose.tools import *
from telewall.core.model import TelephoneNumber

logging.basicConfig(level=logging.WARN)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def test_Anrufer_entsperren_in_web():
    u = inte_testutils.TestUtil()
    u.block_callerid(TelephoneNumber('0790000002'))

    assert u.is_blocked_callerid(TelephoneNumber('0790000002'))
    requests.post('http://localhost/unblock_caller', data={'telephone_number': '0790000002'})
    assert not u.is_blocked_callerid(TelephoneNumber('0790000002'))


if __name__ == '__main__':
    nose.runmodule()
