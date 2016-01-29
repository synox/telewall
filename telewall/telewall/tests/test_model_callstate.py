""" Tests for the CallState class.
"""
import nose
from nose.tools import assert_equals

from telewall.core.model import CallState, TelephoneNumber


def test_callstate_variables():
    c = CallState()
    c.set_caller(TelephoneNumber('+41315080000'))
    assert_equals('0315080000', c.caller.local)


def test_call_state_permit():
    received_events = set()

    def listener(event, call_state):
        received_events.add(call_state.get_current_state())

    c = CallState()
    c.add_listener(listener)
    assert c.is_disconnected

    # disconnected -> ringing
    c.permit()
    assert c.is_ringing
    assert 'ringing' in received_events

    # ringing -> connected
    c.answer()
    assert c.is_connected
    assert 'connected' in received_events

    # connected -> disconnected
    c.hangup()
    assert c.is_disconnected
    assert 'disconnected' in received_events


def test_call_state_refuse():
    received_events = set()

    def listener(event, call_state):
        received_events.add(call_state.get_current_state())

    c = CallState()
    c.add_listener(listener)
    assert c.is_disconnected

    # disconnected -> refusing
    c.refuse()
    assert c.is_refusing
    assert 'refusing' in received_events

    try:
        # refusing -> connected is not possible
        c.answer()
        raise AssertionError('can not trannsition from refusing to connected')
    except:
        pass
    assert c.is_refusing
    assert 'connected' not in received_events

    # refusing -> disconnected
    c.hangup()
    assert c.is_disconnected
    assert 'disconnected' in received_events


def test_call_state_refuse_during_call():
    received_events = set()

    def listener(event, call_state):
        received_events.add(call_state.get_current_state())

    c = CallState()
    c.add_listener(listener)
    assert c.is_disconnected

    # disconnected -> ringing
    c.permit()
    assert c.is_ringing
    assert 'ringing' in received_events

    # ringing -> connected
    c.answer()
    assert c.is_connected
    assert 'connected' in received_events

    received_events = set()

    # connected -> refusing
    c.refuse()
    assert c.is_refusing
    assert 'refusing' in received_events

    assert c.is_refusing
    assert 'connected' not in received_events

    # refusing -> disconnected
    c.hangup()
    assert c.is_disconnected
    assert 'disconnected' in received_events


if __name__ == '__main__':
    nose.runmodule()
