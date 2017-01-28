#!/usr/bin/env python

""" Test suite for ROM class. """

import os
from os.path import isfile
import pytest

from ..rom import ROM

package_dir = os.path.dirname(os.path.abspath(__file__))

ROMPATH = os.path.join(package_dir, "./loremipsum.rom")
MAPPATH = os.path.join(package_dir, "./loremipsum.yml")
OUTPATH = os.path.join(package_dir, "./loremipsum.txt")


def setup_module():
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
    assert ROM(ROM(b'abc')) == ROM(b'abc')


@pytest.fixture(scope="module")
def tinyrom():
    """ Test methods for an explicitly given tiny ROM """
    return ROM(b"a\xffc")


class TestTinyROM:
    def test_repr(self, tinyrom):
        """ Call __repr__ """
        assert tinyrom.__repr__() == "ROM(b'a\\xffc')"


    def test_bytes(self, tinyrom):
        """ Bytestring representation """
        assert bytes(tinyrom) == b"a\xffc"


    def test_str(self, tinyrom):
        """ Unicode string representation """
        assert str(tinyrom) == "ROM(b'a\\xffc')"


    def test_len(self, tinyrom):
        """ Call len(...) on ROM instance """
        assert len(tinyrom) == 3


    def test_eq(self, tinyrom):
        """ Two ROMs constructed from the same bytestring are equal """
        assert tinyrom == ROM(b'a\xffc')


    def test_neq(self, tinyrom):
        """ ROM =/= bytestring """
        assert tinyrom != b'a\xffc'


    def test_index(self, tinyrom):
        """ Find bytestring in ROM """
        assert tinyrom.index(b'\xff') == 1


    @pytest.mark.parametrize("arg, expected", [
        (0, 97),
        (slice(1, 1), ROM(b'')),
        (slice(None, 1), ROM(b'a')),
        (slice(1, 3), ROM(b'\xffc')),
        (slice(None, None), ROM(b'a\xffc')),
    ])
    def test_subscripting(self, tinyrom ,arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert tinyrom[arg] == expected


    @pytest.mark.parametrize("arg, expected", [
        (0, [b'a\xffc']),
        (1, [b'a', b'\xff', b'c']),
        (2, [b'a\xff', b'c']),
        (3, [b'a\xffc']),
        (4, [b'a\xffc']),
    ])
    def test_lines(self, tinyrom, arg, expected):
        """ Split ROM into a list """
        assert tinyrom.lines(arg) == expected


bytes256 = (
    b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"
    b"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f"
    b"\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f"
    b"\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f"
    b"\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f"
    b"\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f"
    b"\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f"
    b"\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f"
    b"\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f"
    b"\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f"
    b"\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf"
    b"\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf"
    b"\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf"
    b"\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf"
    b"\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef"
    b"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff"
)


@pytest.fixture(scope="module")
def rom256():
    """ Test methods for a ROM consiting of every byte value """
    return ROM(bytes256)

class TestROM256:
    def test_repr(self, rom256):
        """ Call __repr__ """
        expected = "ROM(" + repr(bytes256) + ")"
        assert rom256.__repr__() == expected

    def test_bytes(self, rom256):
        """ Bytestring representation """
        assert bytes(rom256) == bytes(range(256))

    def test_str(self, rom256):
        """ Unicode string representation """
        e = r"ROM(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'...b'\xfb\xfc\xfd\xfe\xff')"
        assert str(rom256) == e

#    def test_str_contracted(cls):
#        paramlist = [
#            (-1, ValueError),
#            (0, ValueError),
#            (1, ValueError),
#            (7, ValueError),
#            (8, r"ROM(...)"),
#            (12, r"ROM(b'a'...)"),
#            (15, r"ROM(b'\x00'...)"),
#            (18, r"ROM(b'\x00'...)"),
#            (19, r"ROM(b'\x00\x01'...)"),
#            (19, r"ROM(b'\x00\x01'...)"),
#            (25, r"ROM(b'\x00\x01'...)"),
#            (26, r"ROM(b'\x00\x01'...b'\xff')"),
#        ]
#        for (arg, expected) in paramlist:
#            print(expected is ValueError)
#            if expected is ValueError:
#                yield pytest.raises, ValueError, cls.rom.str_contracted, arg
#            returned = cls.rom.str_contracted(arg)
#            yield assert, returned, expected


    def test_len(self, rom256):
        """ Call len(...) on ROM instance """
        assert len(rom256) == 256


    def test_eq(self, rom256):
        """ Two ROMs constructed from the same bytestring are equal """
        assert rom256 == ROM(bytes(range(256)))


    def test_neq(self, rom256):
        """ ROM =/= bytestring """
        assert rom256 != bytes(range(2**8))


    def test_index(self, rom256):
        """ Find bytestring in ROM """
        assert rom256.index(b'\x80') == 0x80


    @pytest.mark.parametrize("arg, expected", [
        (0, 0),
        (slice(1, 1), ROM(b'')),
        (slice(None, 1), ROM(b'\x00')),
        (slice(1, 3), ROM(b'\x01\x02')),
        (slice(None, None), ROM(bytes256)),
    ])
    def test_subscripting(self, rom256, arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert rom256[arg] == expected


    @pytest.mark.parametrize("arg, expected", [
        (0, [bytes256]),
        (1, [bytes([b]) for b in bytes256]),
        (2, [bytes(bytes256[i:i+2]) for i in range(0, len(bytes256), 2)]),
        (256, [bytes256]),
        (257, [bytes256]),
    ])
    def test_lines(self, rom256, arg, expected):
        """ Split ROM into a list """
        assert rom256.lines(arg) == expected


@pytest.mark.parametrize("args, expected", [
    ([lambda x: x], ROM(b"abc")),
    (["hex"], ["61", "62", "63"]),
    (["hex | join ' '"], "61 62 63"),
    (["hex", "join ' '"], "61 62 63"),
])
def test_pipe(args, expected):
    """ Test ROM:rom.pipe(...) expected output """
    rom = ROM(b'abc')
    returned = rom.pipe(*args)
    assert returned == expected


@pytest.mark.parametrize("args, expected", [
    (["map {}".format(MAPPATH)], "reprehenderit"),
])
def test_pipe2(args, expected):
    rom = ROM(path=ROMPATH)[257:257+13]
    returned = rom.pipe(*args)
    assert returned == expected


def remove_files():
    """ Remove leftover files """
    try:
        os.remove(OUTPATH)
    except IOError:
        pass


@pytest.fixture()
def write_rom_to_file(request):
    mode, pipeline, expected = request.param
    rom = ROM(path=ROMPATH)[257:257+13]
    rom.pipe(pipeline)
    with open(OUTPATH, mode) as outfile:
        returned = outfile.read()
        yield (mode, pipeline, returned, expected)
    remove_files()


@pytest.mark.parametrize("write_rom_to_file", [
    ("rb", "save {}".format(OUTPATH), rb"23623=3\9325<"),
    ("r", "map {} | save {}".format(MAPPATH, OUTPATH), "reprehenderit"),
], indirect=True)
def test_outfile(write_rom_to_file):
    """ Test loading a ROM from a file and write it to another """
    _, _, returned, expected = write_rom_to_file
    assert returned == expected


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


@pytest.fixture(scope="function")
def execution(request):
    stream, filterstr, expected = request.param
    filtr = ROM.execute(filterstr)
    returned = filtr(stream)
    yield (returned, expected)
    remove_files()


@pytest.mark.parametrize("execution", [
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
], indirect=True)
def test_execute(execution):
    """ Test ROM.execute(execstr) """
    returned, expected = execution
    assert returned == expected
