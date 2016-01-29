""" test the util module.

"""

import os
from xml.etree import ElementTree

import nose
from nose.tools import *

from telewall.core import phonebook
from telewall.core.model import TelephoneNumber
from telewall.core.util import get_cisco_spa232D_md5


def test_spa232d_md5():
    md5 = get_cisco_spa232D_md5('admin')
    assert_equals('498836900e3cb4d343b96f3f1c578f4a', md5)


if __name__ == '__main__':
    nose.runmodule()
