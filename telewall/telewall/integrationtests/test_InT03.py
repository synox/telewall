""" Integration test: block caller in web app
"""
import os
import sys
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import logging

import requests
from nose.tools import *
import nose
import inte_testutils
from telewall.core.model import TelephoneNumber


logging.basicConfig(level=logging.WARN)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def test_Anrufer_sperren_in_web():
    u = inte_testutils.TestUtil()
    u.unblock_callerid(TelephoneNumber('0790000003'))

    assert not u.is_blocked_callerid(TelephoneNumber('0790000003'))
    requests.post('http://localhost/block_caller', data={'telephone_number': '0790000003'})
    assert u.is_blocked_callerid(TelephoneNumber('0790000003'))


if __name__ == '__main__':
    nose.runmodule()
