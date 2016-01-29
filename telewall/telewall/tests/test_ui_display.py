""" Tests the user interface display class.
"""
import nose
from nose.tools import *

from telewall.ui.display import Display


def test_short_line_noscroll():
    line = Display.Line('Telewall')
    assert_equals('Telewall        ', line.get())

    line.scroll()
    assert_equals('Telewall        ', line.get())


def test_short_line_scroll():
    line = Display.Line('Telewall', scroll=True)
    assert_equals('Telewall        ', line.get())

    line.scroll()
    assert_equals('Telewall        ', line.get())


def test_long_line_noscroll():
    line = Display.Line('Telewall, funktioniert.', scroll=False)
    assert_equals('Telewall, funkti', line.get())

    line.scroll()
    assert_equals('Telewall, funkti', line.get())


def test_long_line_scroll():
    line = Display.Line('Telewall, funktioniert.', scroll=True)
    assert_equals('Telewall, funkti', line.get())
    line.scroll()
    assert_equals('elewall, funktio', line.get())
    for i in range(5):
        line.scroll()
    assert_equals('ll, funktioniert', line.get())
    for i in range(5):
        line.scroll()
    assert_equals('unktioniert. - T', line.get())
    for i in range(10):
        line.scroll()
    assert_equals('t. - Telewall, f', line.get())
    for i in range(5):
        line.scroll()
    # one full loop
    assert_equals('Telewall, funkti', line.get())
    line.scroll()
    assert_equals('elewall, funktio', line.get())

    line.scroll()


if __name__ == '__main__':
    nose.runmodule()
