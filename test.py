#!/usr/bin/env python

""" Test suite for ROM class. """

from reader import ROM
import os
from os.path import isfile
from nose.tools import assert_equal, assert_not_equal

ROMPATH = "./majin-tensei-ii/mt2.sfc"
MAPPATH = "./majin-tensei-ii/hexmap.yaml"
OUTPATH = "./romtexttest.txt"


def set_up():
    """ Assert that certain files are present for testing """
    assert isfile(ROMPATH)
    assert isfile(MAPPATH)


def test_init1():
    """ Call constructor with sample data """
    ROM(b'abc')


def test_init2():
    """ Call constructor with sample path """
    ROM(path=ROMPATH)


def test_repr():
    """ Call __repr__ """
    rom = ROM(b'abc')
    assert_equal(rom.__repr__(), "ROM(b'abc')")


def test_len():
    """ Call len(...) on ROM instance """
    rom = ROM(b'abc')
    assert_equal(len(rom), 3)


def test_eq():
    """ ROM instance equality """
    rom = ROM(b'abc')
    yield assert_equal, rom, ROM(b'abc')
    yield assert_not_equal, rom, b'abc'


def test_subscripting():
    """ Subscripting support, similar to a bytestring """
    rom = ROM(b'abcde')
    paramlist = [
        (rom[0], 97),
        (rom[1:1], ROM(b'')),
        (rom[:1], ROM(b'a')),
        (rom[1:4], ROM(b'bcd')),
        (rom[:], rom),
    ]
    for (returned, expected) in paramlist:
        yield assert_equal, returned, expected


def test_bytes():
    """ Bytestring representation """
    rom = ROM(b'abc')
    assert_equal(str(rom), "61 62 63")


def test_str():
    """ Unicode string representation """
    rom = ROM(b'abc')
    assert_equal(str(rom), "61 62 63")


def assert_equal2(returned, expected):
    """ Clearer assert function """
    assert returned == expected, ("""
Returned:\n[{}]
Expected:\n[{}]
    """.format(returned, expected))


def test_execute():
    """ Test ROM.execute(execstr) expected output """
    tables = [
        """\
+-+-+-+
|a|b|c|
|d|e|f|
|g| | |
+-+-+-+""",
        """\
+---+---+---+
| a | b | c |
| d | e | f |
| g |   |   |
+---+---+---+""",
    ]
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
        ("abcdefg", "tabulate 3 --label", "0: abc\n3: def\n6: g  "),
        ("abcdefg", "tabulate 3 -l", "0: abc\n3: def\n6: g  "),
        ("abcdefghijklmn", "tabulate 3 -l", """\
 0: abc
 3: def
 6: ghi
 9: jkl
12: mn """),
        ("abcdefg", "tabulate 3 --border", tables[0]),
        ("abcdefg", "tabulate 3 -b", tables[0]),
        ("abcdefg", "tabulate 3 -b --padding 1", tables[1]),
        ("abcdefg", "tabulate 3 -b -p 1", tables[1]),
    ]
    for (stream, filterstr, expected) in paramlist:
        filtr = ROM.execute(filterstr)
        returned = filtr(stream)
        yield assert_equal2, returned, expected


def test_pipe():
    """ Test ROM:rom.pipe(...) expected output """
    rom1 = ROM(b'abc')
    paramlist1 = [
        ([lambda x: x], ROM(b"abc")),
        (["hex"], ["61", "62", "63"]),
        (["hex | join ' '"], "61 62 63"),
        (["hex", "join ' '"], "61 62 63"),
    ]
    for (pipeline, expected) in paramlist1:
        returned = rom1.pipe(*pipeline)
        yield assert_equal, returned, expected
    offset = 0x2f0280+50
    rom2 = ROM(path=ROMPATH)[offset:offset+10]
    paramlist2 = [
        (["map {}".format(MAPPATH)], "A T L U S "),
    ]
    for (pipeline, expected) in paramlist2:
        returned = rom2.pipe(*pipeline)
        yield assert_equal, returned, expected


def test_outfile():
    """ Test loading a ROM from a file and write it to another """
    offset = 0x2f0200
    rom = ROM(path=ROMPATH)[offset:offset+0x100]
    rom.pipe("save {}".format(OUTPATH))
    with open(OUTPATH, 'rb') as outfile:
        returned = outfile.read()
        expected = rom.content
        assert_equal(returned, expected)
    os.remove(OUTPATH)
    rom.pipe("map {} | save {}".format(MAPPATH, OUTPATH))
    with open(OUTPATH, 'r', encoding="utf8") as outfile:
        returned = outfile.read()
        expected = rom.pipe("map {}".format(MAPPATH))
        assert_equal(returned, expected)
    os.remove(OUTPATH)


def teardown():
    """ Remove leftover files """
    try:
        os.remove(OUTPATH)
    except IOError:
        pass
