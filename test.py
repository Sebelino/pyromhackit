#!/usr/bin/env python

from nose.tools import assert_equal, assert_not_equal
from reader import ROM
from os.path import isfile
import os

ROMPATH = "./majin-tensei-ii/mt2.sfc"
MAPPATH = "./majin-tensei-ii/hexmap.yaml"
OUTPATH = "./romtexttest.txt"


def setUp():
    assert isfile(ROMPATH)
    assert isfile(MAPPATH)


def test_init1():
    ROM(b'abc')


def test_init2():
    ROM(path=ROMPATH)


def test_repr():
    r = ROM(b'abc')
    assert_equal(r.__repr__(), "ROM(b'abc')")


def test_len():
    r = ROM(b'abc')
    assert_equal(len(r), 3)


def test_eq():
    r = ROM(b'abc')
    yield assert_equal, r, ROM(b'abc')
    yield assert_not_equal, r, b'abc'


def test_subscripting():
    r = ROM(b'abcde')
    paramlist = [
        (r[0], 97),
        (r[1:1], ROM(b'')),
        (r[:1], ROM(b'a')),
        (r[1:4], ROM(b'bcd')),
        (r[:], r),
    ]
    for (returned, expected) in paramlist:
        yield assert_equal, returned, expected


def test_str():
    r = ROM(b'abc')
    assert_equal(str(r), "61 62 63")


#def test_table():
#    r = ROM(b'abcdefg')
#    paramlist = [
#        ((0, False, ROM.hex), "61 62 63 64 65 66 67"),
#        ((3, False, ROM.hex), "61 62 63\n64 65 66\n67"),
#        ((3, False, ROM.latin1), "a b 63\n64 65 66\n67"),
#    ]
#    for (params, expected) in paramlist:
#        yield assert_equal, returned, expected

def assert_equal2(returned, expected):
    assert returned == expected, ("""
Returned:\n[{}]
Expected:\n[{}]
    """.format(returned, expected))


def test_execute():
    table = """\
+---+---+---+
| a | b | c |
| d | e | f |
| g |   |   |
+---+---+---+"""
    paramlist = [
        (b"abc", "latin1", "abc"),
        (b"abc", "hex", ["61", "62", "63"]),
        (b"abc", "odd", b"ac"),
        (["a", "bb", "c"], "join", "abbc"),
        (["a", "bb", "c"], "join ' '", "a bb c"),
        (["a", "bb", "c"], "join __", "a__bb__c"),
        (b"\x0b\x00\x1e\x00\x16\x00\x1f\x00\x1d\x00",
         "map {}".format(MAPPATH), "A T L U S "),
        ("abcdefg", "tabulate 3", "abc\ndef\ng  "),
        ("abcdefg", "tabulate 3 --label", "0: abc\n3: def\n6: g"),
#        ("abcdefg", "tabulate 3 -l", "0: abc\n3: def\n6: g"),
#        ("abcdefg", "tabulate 3 --border", table),
#        ("abcdefg", "tabulate 3 -b", table),
    ]
    for (stream, filter, expected) in paramlist:
        f = ROM.execute(filter)
        returned = f(stream)
        print("Returned\n[{}]".format(returned))
        print("Expected\n[{}]".format(expected))
        yield assert_equal2, returned, expected


def test_pipe():
    r1 = ROM(b'abc')
    paramlist1 = [
        ([lambda x: x], ROM(b"abc")),
        (["hex"], ["61", "62", "63"]),
        (["hex | join ' '"], "61 62 63"),
        (["hex", "join ' '"], "61 62 63"),
    ]
    for (pipeline, expected) in paramlist1:
        returned = r1.pipe(*pipeline)
        yield assert_equal, returned, expected
    offset = 0x2f0280+50
    r2 = ROM(path=ROMPATH)[offset:offset+10]
    paramlist2 = [
        (["map {}".format(MAPPATH)], "A T L U S "),
    ]
    for (pipeline, expected) in paramlist2:
        returned = r2.pipe(*pipeline)
        yield assert_equal, returned, expected


def test_outfile():
    offset = 0x2f0200
    r = ROM(path=ROMPATH)[offset:offset+0x100]
    r.pipe("save {}".format(OUTPATH))
    with open(OUTPATH, 'rb') as f:
        returned = f.read()
        expected = r.content
        assert_equal(returned, expected)
    os.remove(OUTPATH)
    r.pipe("map {} | save {}".format(MAPPATH, OUTPATH))
    with open(OUTPATH, 'r', encoding="utf8") as f:
        returned = f.read()
        expected = r.pipe("map {}".format(MAPPATH))
        assert_equal(returned, expected)
    os.remove(OUTPATH)


def teardown():
    try:
        os.remove(OUTPATH)
    except IOError:
        pass
