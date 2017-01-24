#!/usr/bin/env python

""" Test suite for ROM class. """

from ..rom import ROM
import os
from os.path import isfile
from nose.tools import assert_equal, assert_not_equal

package_dir = os.path.dirname(os.path.abspath(__file__))

ROMPATH = os.path.join(package_dir, "./loremipsum.rom")
MAPPATH = os.path.join(package_dir, "./loremipsum.yml")
OUTPATH = os.path.join(package_dir, "./loremipsum.txt")


def assert_equal2(returned, expected):
    """ Clearer assert function """
    assert returned == expected, ("""
Returned:\n[{}]
Expected:\n[{}]
    """.format(returned, expected))


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


def test_idempotence():
    """ ROM(ROM(bs)) == ROM(bs) for all bytestrings bs """
    assert_equal(ROM(ROM(b'abc')), ROM(b'abc'))


class TestTinyROM(object):
    """ Test methods for an explicitly given tiny ROM """

    @classmethod
    def setup_class(cls):
        """ Construct a sample short ROM """
        cls.rom = ROM(b'abc')

    def test_repr(cls):
        """ Call __repr__ """
        assert_equal(cls.rom.__repr__(), "ROM(b'abc')")

    def test_bytes(cls):
        """ Bytestring representation """
        assert_equal(bytes(cls.rom), b"abc")

    def test_str(cls):
        """ Unicode string representation """
        assert_equal(str(cls.rom), "61 62 63")

    def test_len(cls):
        """ Call len(...) on ROM instance """
        assert_equal(len(cls.rom), 3)

    def test_eq(cls):
        """ Two ROMs constructed from the same bytestring are equal """
        assert_equal(cls.rom, ROM(b'abc'))

    def test_neq(cls):
        """ ROM =/= bytestring """
        assert_not_equal(cls.rom, b'abc')

    def test_index(cls):
        """ Find bytestring in ROM """
        assert_equal(cls.rom.index(b'b'), 1)

    def test_subscripting(cls):
        """ Subscripting support is isomorphic to bytestrings """
        paramlist = [
            (cls.rom[0], 97),
            (cls.rom[1:1], ROM(b'')),
            (cls.rom[:1], ROM(b'a')),
            (cls.rom[1:3], ROM(b'bc')),
            (cls.rom[:], cls.rom),
        ]
        for (returned, expected) in paramlist:
            yield assert_equal, returned, expected

    def test_lines(cls):
        """ Split ROM into a list """
        paramlist = [
            ([0], [b'abc']),
            ([1], [b'a', b'b', b'c']),
            ([2], [b'ab', b'c']),
            ([3], [b'abc']),
            ([4], [b'abc']),
        ]
        for (args, expected) in paramlist:
            returned = cls.rom.lines(*args)
            yield assert_equal, returned, expected

    def test_decode(cls):
        """ Decode ROM into a string using codecs """
        paramlist = [
            (["Hexify"], "616263"),
            (["HexifySpaces"], "61 62 63"),
            (["ASCII"], "abc"),
            (["MonospaceASCII"], "abc"),
            (["Mt2GarbageTextPair"], "カクb"),
        ]
        for args, expected in paramlist:
            returned = cls.rom.decode(*args)
            yield assert_equal, returned, expected


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
    offset = 257
    rom2 = ROM(path=ROMPATH)[offset:offset+13]
    paramlist2 = [
        (["map {}".format(MAPPATH)], "reprehenderit"),
    ]
    for (pipeline, expected) in paramlist2:
        returned = rom2.pipe(*pipeline)
        yield assert_equal, returned, expected


def test_outfile():
    """ Test loading a ROM from a file and write it to another """
    offset = 257
    rom = ROM(path=ROMPATH)[offset:offset+13]
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


def test_execute():
    """ Test ROM.execute(execstr) """
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
        (b"01234 56784",
         "map {}".format(MAPPATH), "Lorem ipsum"),
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


def teardown():
    """ Remove leftover files """
    try:
        os.remove(OUTPATH)
    except IOError:
        pass
