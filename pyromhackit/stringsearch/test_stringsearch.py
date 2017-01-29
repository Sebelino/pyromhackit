#!/usr/bin/env python

import pytest


def locations(content):
    return [(content.index(b"HELLO"), len("HELLO"))]


@pytest.mark.parametrize("bytestr, expected", [
    (b"\x00\x10\x42 HELLO \x89\x32", [(4, 5)]),
])
def test_findscript(bytestr, expected):
    returned = locations(bytestr)
    assert returned == expected
