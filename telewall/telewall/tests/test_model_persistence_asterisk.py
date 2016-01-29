"""
Tests the Telewall asterisk-persistence.
"""
from datetime import datetime, timedelta

import nose
from nose.tools import *

from telewall.core.config import Config
from telewall.core.model import AsteriskPersistence
from telewall.core.model import CallRecord
from telewall.core.testutils import create_temp_asterisk_db


def test_get_last_caller():
    asterisk_db = create_temp_asterisk_db(sample_data=True, overwrite=True)
    with AsteriskPersistence(asterisk_db, print_sql=True) as p:
        now = datetime.now()
        anruf = CallRecord(src='0311112233', start=now, end=now, dcontext='incoming',
                           clid='123', channel='123', dstchannel='123', lastapp='123', lastdata='123', duration='123',
                           billsec='123', disposition='123', blocked='123')
        p.persist(anruf)

        result = p.get_last_cdr_callerid()
        assert_is_not_none(result)
        assert_equals('0311112233', result.src)


def test_init_testdb_with_samples():
    asterisk_db = create_temp_asterisk_db(sample_data=True, overwrite=True)
    with AsteriskPersistence(asterisk_db, print_sql=False) as p:
        result = p.get_call_history()
        assert_is_not_none(result)
        assert len(result) >= 0


def test_cleanup_old_call_records():
    asterisk_db = create_temp_asterisk_db(sample_data=False, overwrite=True)

    with AsteriskPersistence(asterisk_db, print_sql=False) as p:
        Config.CALL_HISTORY_KEEP_DAYS = 10
        time_ok = datetime.now() - timedelta(days=9)
        time_old = datetime.now() - timedelta(days=10, hours=2)

        record_ok = CallRecord(src='0999999', start=time_ok, end=time_ok, dcontext='incoming',
                               clid='123', channel='123', dstchannel='123', lastapp='123', lastdata='123',
                               duration='123',
                               billsec='123', disposition='123', blocked='123')
        record_old = CallRecord(src='012345', start=time_old, end=time_old, dcontext='incoming',
                                clid='123', channel='123', dstchannel='123', lastapp='123', lastdata='123',
                                duration='123',
                                billsec='123', disposition='123', blocked='123')

        p.persist(record_ok)
        p.persist(record_old)

        assert_equals(p.get_call_history_count(), 2)

        p.delete_old_call_records()
        assert_equals(p.get_call_history_count(), 1)

        list = p.get_call_history()
        assert_equals(list[0].src, '0999999')


if __name__ == '__main__':
    nose.runmodule()
