""" Test for the telewall (blocked callers) persistence.
"""
import nose
from nose.tools import *

from telewall.core.model import Persistence, TelephoneNumber
from telewall.core.testutils import create_temp_telewall_db


def test_block_caller():
    db_path  = create_temp_telewall_db(overwrite=True)
    with Persistence(db_path) as p:
        result = p.block(TelephoneNumber('0311238899'), 'John', 'Unit-Test')
        assert_equals('+41311238899', result.telephone_number)
        assert_equals('John', result.comment)
        assert_equals('Unit-Test', result.source)


def test_is_blocked():
    db_path  = create_temp_telewall_db(overwrite=True)
    with Persistence(db_path) as p:
        assert_false(p.is_blocked(TelephoneNumber('0311112233')))
        p.block(TelephoneNumber('0311112233'), 'John', 'Unit-Test')
        assert_true(p.is_blocked(TelephoneNumber('0311112233')))


@raises(AssertionError)
def test_is_blocked_invalid():
    db_path  = create_temp_telewall_db(overwrite=True)
    with Persistence(db_path) as p:
        p.is_blocked('0311112233')  # should be number, not string


def test_unblock_caller():
    db_path  = create_temp_telewall_db(overwrite=True)
    with Persistence(db_path) as p:
        p.block(TelephoneNumber('0311112233'), 'John', 'Unit-Test')
        p.unblock(TelephoneNumber('0311112233'))
        assert_false(p.is_blocked(TelephoneNumber('0311112233')))


def test_get_all_blocked():
    db_path  = create_temp_telewall_db(overwrite=True)
    with Persistence(db_path) as p:
        n1 = p.block(TelephoneNumber('0311112233'), 'John', 'Unit-Test')
        n2 = p.block(TelephoneNumber('0315555'), 'John', 'Unit-Test')
        all = p.get_all_blocked()
        assert_equals(2, len(all))
        assert_equals(n2, all[0])
        assert_equals(n1, all[1])

if __name__ == '__main__':
    nose.runmodule()