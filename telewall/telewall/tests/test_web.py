# coding=utf8
""" Test for the web-application. The application is not really run on a tcp port, but the real code is executed.
"""
from __future__ import print_function
import logging
import unittest
import nose

from nose.tools import assert_equals

import telewall.core.testutils
from telewall.web.web import app as webapp

logging.basicConfig(level=logging.WARN)
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        webapp.config['TELEWALL_DATABASE_PATH'] = telewall.core.testutils.create_temp_telewall_db(overwrite=True)
        webapp.config['ASTERISK_DATABASE_PATH'] = telewall.core.testutils.create_temp_asterisk_db(overwrite=True)
        webapp.config['TESTING'] = True
        self.app = webapp.test_client()

    def tearDown(self):
        pass

    def _block_caller(self, telephone_number, comment='', next_page='blocked_callers'):
        return self.app.post('/block_caller', data=dict(
            telephone_number=telephone_number,
            comment=comment,
            next_page=next_page
        ), follow_redirects=True)

    def _unblock_caller(self, telephone_number, next_page='blocked_callers'):
        return self.app.post('/unblock_caller', data=dict(
            telephone_number=telephone_number,
            next_page=next_page
        ), follow_redirects=True)

    def test_that_root_is_redirected(self):
        resp = self.app.get('/')
        assert resp.status_code == 302

    def test_empty_call_history(self):
        resp = self.app.get('/call_history')
        assert 'eingehenden Anrufe protokolliert' in resp.data

    def test_empty_blocked_callers(self):
        resp = self.app.get('/blocked_callers')
        assert 'keine Anrufer gesperrt' in resp.data

    def test_block_caller(self):
        resp = self._block_caller('0314445566', 'XYZ Marketing')
        assert_equals(200, resp.status_code)
        assert '0314445566 wurde gesperrt' in resp.data
        assert '0314445566' in resp.data
        assert 'XYZ Marketing' in resp.data

    def test_block_already_blocked(self):
        resp = self._block_caller('0314445566', 'XYZ Marketing')
        resp = self._block_caller('0314445566', 'XYZ Marketing')
        assert 'ist bereits gesperrt' in resp.data

    def test_block_with_spaces(self):
        resp = self._block_caller('031 444 55 66', 'XYZ Marketing')
        assert '0314445566' in resp.data
        assert 'XYZ Marketing' in resp.data

    def test_block_mobile(self):
        resp = self._block_caller('+41795557799', 'Hans Muster')
        assert '0795557799' in resp.data
        assert 'Hans Muster' in resp.data

    def test_block_not_plausible_number(self):
        resp = self._block_caller('+99942373242', 'ABC')
        LOG.debug(resp.data.decode('utf-8'))
        assert u'ist ungültig' in resp.data.decode('utf-8')

    def test_block_not_a_number(self):
        resp = self._block_caller('Hans Muster', 'ABC')
        assert u'ist ungültig' in resp.data.decode('utf-8')

    def test_block_redirect_blocked_callers(self):
        resp = self._block_caller('031 444 55 66', next_page='blocked_callers')
        assert 'class="active"><a href="blocked_callers">' in resp.data

    def test_block_redirect_call_history(self):
        resp = self._block_caller('031 444 55 66', next_page='call_history')
        LOG.debug(resp.data)
        assert 'class="active"><a href="call_history">' in resp.data

    def test_unblock_caller(self):
        resp = self._block_caller('031 444 55 66', 'XYZ Marketing')
        resp = self._unblock_caller('0314445566')
        resp = self.app.get('/blocked_callers')
        assert '314445566' not in resp.data
        assert 'XYZ Marketing' not in resp.data

    def test_unblock_unknown_ignored(self):
        resp = self._unblock_caller('0314445599')
        assert 'war bereits entsperrt' in resp.data

    def test_unblock_redirect_blocked_callers(self):
        resp = self._block_caller('031 444 55 66', 'XYZ Marketing')
        resp = self._unblock_caller('0314445566', next_page='blocked_callers')
        assert 'class="active"><a href="blocked_callers">' in resp.data

    def test_unblock_redirect_call_history(self):
        resp = self._block_caller('031 444 55 66', 'XYZ Marketing')
        resp = self._unblock_caller('0314445566', next_page='call_history')
        assert 'class="active"><a href="call_history">' in resp.data


if __name__ == '__main__':
    nose.runmodule()
