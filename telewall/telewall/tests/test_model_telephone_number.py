""" Tests the TelephoneNumber class.
"""
import nose
from nose.tools import *

from telewall.core.model import TelephoneNumber


def test_national_number():
    n = TelephoneNumber('0315081100')
    assert_equals('+41315081100', n.full)
    assert_equals('0315081100', n.local)
    assert_equals(True, n.is_valid)


def test_national_number_with_prefix():
    n = TelephoneNumber('+41315081100')
    assert_equals('+41315081100', n.full)
    assert_equals('0315081100', n.local)
    assert_equals(True, n.is_valid)


def test_mobile_number_with_prefix():
    n = TelephoneNumber('+41794447788')
    assert_equals('+41794447788', n.full)
    assert_equals('0794447788', n.local)
    assert_equals(True, n.is_valid)


def test_foreign_number():
    n = TelephoneNumber('004930355820')
    assert_equals('+4930355820', n.full)
    assert_equals('+4930355820', n.local)
    assert_equals(True, n.is_valid)


def test_should_handle_invalid_country():
    n = TelephoneNumber('00215880183', validate=True)
    assert_equals('+215880183', n.full)
    assert_equals('+215880183', n.local)
    assert_equals(False, n.is_valid)


def test_handle_invalid_number():
    n = TelephoneNumber('0000', validate=True)
    assert_equals(False, n.is_valid)


def test_handle_invalid_number2():
    n = TelephoneNumber('0004', validate=True)
    assert_equals(False, n.is_valid)


def test_handle_invalid_number3():
    n = TelephoneNumber('999', validate=True)
    assert_equals(False, n.is_valid)


def test_handle_emergency_number():
    n = TelephoneNumber('112', validate=True)
    assert_equals(False, n.is_valid)
    # it's ok that this number can not be blocked.


# the following block allows to conduct performance tests, uncomment if required.
#
# def test_number_parse_performance():
#     with Timer(verbose=False):
#         for i in range(50000):
#             n = TelephoneNumber('+41123233221', validate=False)
#
#     assert False
#
#
# class Timer(object):
#     def __init__(self, verbose=False):
#         self.verbose = verbose
#
#     def __enter__(self):
#         self.start = time.time()
#         return self
#
#     def __exit__(self, *args):
#         self.end = time.time()
#         self.secs = self.end - self.start
#         self.msecs = self.secs * 1000  # millisecs
#         if self.verbose:
#             print 'elapsed time: %f ms' % self.msecs

if __name__ == '__main__':
    nose.runmodule()
