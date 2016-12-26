#!/usr/bin/env python

from nose.tools import assert_equals


def test_findscript():
    paramlist = [
        (b"\x00\x10\x42 HELLO \x89\x32", [(4, 5)]),
    ]
    for (param, expected) in paramlist:
        returned = locations(param)
        yield assert_equals, returned, expected
