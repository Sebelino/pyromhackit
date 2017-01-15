#!/usr/bin/env python

"""
Tests for checking the bijective property of codecs.
"""

from nose.tools import assert_equal
from .codec import MonospaceASCII


def test_bijection():
    yield assert_equal, MonospaceASCII.decode(b'a'), 'a'
    yield assert_equal, MonospaceASCII.decode(b'\t'), 'ĉ'
