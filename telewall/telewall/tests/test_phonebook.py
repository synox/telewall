""" test the phonebook. There are offline tests for parsing the xml as well as online tests to make real
lookup requests.

For some tests mock code is injected into the code in order to test the method offline.
"""

import os
from xml.etree import ElementTree

import nose
from nose.tools import *

from telewall.core import phonebook
from telewall.core.model import TelephoneNumber

run_online_tests = False


def test_existing_number_found():
    def _query_mock(number):
        return read_xml('tel_search_ch-success.xml')

    _query_orginal = phonebook._query
    phonebook._query = _query_mock
    try:
        n = TelephoneNumber('032 321 61 11')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_true(result.success)
        assert_equals('Berner Fachhochschule, Technik & Informatik', result.name)
        assert_false(result.is_corrected)
    finally:
        phonebook._query = _query_orginal


def test_wrong_number_notfound():
    def _query_mock(number):
        return read_xml('tel_search_ch-noresult.xml')

    _query_orginal = phonebook._query
    try:
        phonebook._query = _query_mock

        n = TelephoneNumber('031 000 11 22')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_false(result.success)

    finally:
        phonebook._query = _query_orginal


def test_companynumber_correction():
    mockresults = [read_xml('tel_search_ch-correction.xml'), read_xml('tel_search_ch-correction-result.xml')]
    mockresults.reverse()

    def _query_mock(number):
        return mockresults.pop()

    _query_orginal = phonebook._query
    phonebook._query = _query_mock
    try:
        n = TelephoneNumber('032 321 64 63')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_true(result.success)
        assert_equals('Berner Fachhochschule, Technik und Informatik', result.name)
        assert_true(result.is_corrected)

    finally:
        phonebook._query = _query_orginal


# the following test works only when online:
def test_existing_number_found_online():
    if run_online_tests:
        n = TelephoneNumber('032 321 61 11')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_true(result.success)
        assert_equals('Berner Fachhochschule, Technik & Informatik', result.name)
        assert_false(result.is_corrected)


# the following test works only when online:
def test_wrong_number_notfound_online():
    if run_online_tests:
        n = TelephoneNumber('033 999 99 99')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_false(result.success)


# the following test works only when online:
def test_companynumber_correction_online():
    if run_online_tests:
        n = TelephoneNumber('032 321 64 63')
        result = phonebook.lookup(n)
        print(result)
        assert_is_not_none(result)
        assert_true(result.success)
        assert_equals('Berner Fachhochschule, Technik und Informatik', result.name)
        assert_true(result.is_corrected)


def test_get_correction_when_available():
    root = read_xml('tel_search_ch-correction.xml')

    result = phonebook._find_correction(root)
    assert_equals('032 321 61 **', result)


def test_get_correction_when_not_available():
    root = read_xml('tel_search_ch-success.xml')

    result = phonebook._find_correction(root)
    assert_is_none(result)


def test_get_name_when_available():
    root = read_xml('tel_search_ch-success.xml')

    result = phonebook._find_name(root)
    assert_equals('Berner Fachhochschule, Technik & Informatik', result)


def test_get_name_when_not_available():
    root = read_xml('tel_search_ch-correction.xml')

    result = phonebook._find_name(root)
    assert_is_none(result)


def read_xml(filename):
    absolute_filename = os.path.join(os.path.dirname(__file__), 'data', filename)
    return ElementTree.parse(absolute_filename)


if __name__ == '__main__':
    nose.runmodule()
