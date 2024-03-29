#!/usr/bin/env python

""" Test suite for ROM class. """
import os
import tempfile
from os.path import isfile
import re
import pytest

from pyromhackit.rom import ROM
from pyromhackit.topology.simple_topology import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))

ROMPATH = os.path.join(package_dir, "./loremipsum.rom")
MAPPATH = os.path.join(package_dir, "./loremipsum.yml")
OUTPATH = os.path.join(package_dir, "./loremipsum.txt")


def setup_module():
    """ Assert that certain files are present for testing """
    assert isfile(ROMPATH)
    assert isfile(MAPPATH)


def test_init_bytestring():
    """ Call constructor with sample data """
    ROM(b'abc')


def test_init_path():
    """ Call constructor with sample path """
    ROM(ROMPATH)


def test_init_intlist():
    """ Call constructor with list of byte values """
    ROM([0, 97, 98, 99, 255])


def test_init_int():
    """ Isomorphic to bytes(int) """
    ROM(7)


def test_init_fail():
    """ Call constructor with invalid value """
    with pytest.raises(ValueError):
        ROM([256])
    with pytest.raises(TypeError):
        ROM(None)


def test_idempotence():
    """ ROM(ROM(bs)) == ROM(bs) for all bytestrings bs """
    assert ROM(ROM(b'abc')) == ROM(b'abc')


class TestTinyROM:
    @pytest.fixture(scope="function")
    def tinyrom(self) -> ROM:
        """ Test methods for an explicitly given tiny ROM """
        return ROM(b"a\xffc")

    def test_repr(self, tinyrom):
        """ Call __repr__ """
        rpr = tinyrom.__repr__()
        repr_regex = r"<pyromhackit\.rom.ROM object at 0x(\d|\w)+>"
        assert re.search(repr_regex, rpr)

    def test_bytes(self, tinyrom):
        """ Bytestring representation """
        assert bytes(tinyrom) == b"a\xffc"

    def test_str(self, tinyrom):
        """ Unicode string representation """
        assert str(tinyrom) == "ROM(b'a\\xffc')"

    def test_len(self, tinyrom):
        """ Call len(...) on ROM instance """
        assert len(tinyrom) == 3

    def test_atomcount(self, tinyrom):
        assert tinyrom.atomcount() == 3

    def test_eq(self, tinyrom):
        """ Two ROMs constructed from the same bytestring are equal """
        assert tinyrom == ROM(b'a\xffc')

    def test_ne(self, tinyrom):
        """ ROM =/= bytestring """
        assert tinyrom != b'a\xffc'

    def test_lt(self, tinyrom):
        """ ROM inequality is isomorphic to that of bytestrings """
        assert tinyrom < ROM(b'a\xffd')
        assert tinyrom > ROM(b'a\xffb')

    def test_hash(self, tinyrom):
        """ ROM hash = the hash of its repr """
        assert hash(tinyrom) == hash(b'a\xffc')

    def test_index(self, tinyrom):
        """ Find bytestring in ROM """
        assert tinyrom.index(b'\xff') == 1

    @pytest.mark.parametrize("bregex, expected", [
        (b'a', (0, 1)),
        (b'\xff', (1, 2)),
        (b'c', (2, 3)),
        (b'a.', (0, 2)),
        (b'a.c', (0, 3)),
        (b'.*', (0, 3)),
        (b'.*c', (0, 3)),
        (b'd', None),
    ])
    def test_index_regex(self, tinyrom, bregex, expected):
        """ Find bytestring in ROM using regex """
        assert tinyrom.index_regex(bregex) == expected

    @pytest.mark.parametrize("n, expected", [
        (0, b'a\xffc'),
        (1, b'b\x00d'),
        (255, b'`\xfeb'),
    ])
    def test_offset(self, tinyrom, n, expected):
        """ Find bytestring in ROM using relative search """
        assert tinyrom.offset(n) == ROM(expected)

    @pytest.mark.parametrize("bregex, stop_on_match, expected", [
        (b'not', False, dict()),
        (b'not', True, dict()),
        (b'a\xffc', False, {0: (0, 3)}),
        (b'a\xffc', True, {0: (0, 3)}),
        (b'\xffc', False, {0: (1, 3)}),
        (b'\xffc', True, {0: (1, 3)}),
        (b'\x00d', False, {1: (1, 3)}),
        (b'\x00d', True, {1: (1, 3)}),
        (b'D.F', False, {227: (0, 3)}),
        (b'D.F', True, {227: (0, 3)}),
    ])
    def test_relative_search(self, tinyrom, bregex, stop_on_match, expected):
        """ Find bytestring in ROM using relative search """
        assert tinyrom.relative_search(bregex, stop_on_match) == expected

    @pytest.mark.parametrize("arg, expected", [
        (0, b'a'),
    ])
    def test_subscripting(self, tinyrom, arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert tinyrom[arg] == expected

    @pytest.mark.parametrize("arg, expected", [
        # (slice(1, 1), b''),  # mmap trouble
        (slice(None, 1), b'a'),
        (slice(1, 3), b'\xffc'),
        (slice(None, None), b'a\xffc'),
        (slice(None, 5), b'a\xffc'),
        # (slice(4, 5), b''),  # mmap trouble
    ])
    def test_subscripting_slices(self, tinyrom, arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert tinyrom[arg] == expected

    def test_subscripting_raises(self, tinyrom):
        """ Subscripting support is isomorphic to bytestrings """
        with pytest.raises(TypeError) as excinfo:
            tinyrom[(1, 3)]

    def test_convert_to_bytes(self, tinyrom):
        assert bytes(tinyrom) == b"a\xffc"

    def test_concat_bytes(self, tinyrom):
        assert b'123' + tinyrom == ROM(b'123a\xffc')
        assert tinyrom + b'123' == ROM(b'a\xffc123')

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

    def test_coverup(self, tinyrom: ROM):
        tinyrom.coverup(0, 1)
        assert bytes(tinyrom) == b'\xffc'

    def test_coverup_and_reveal(self, tinyrom: ROM):
        tinyrom.coverup(0, 1)
        tinyrom.reveal(0, 1)
        assert bytes(tinyrom) == b'a\xffc'

    def test_coverup_all_and_reveal_all(self, tinyrom: ROM):
        tinyrom.coverup(None, None)
        tinyrom.reveal(None, None)
        assert bytes(tinyrom) == b'a\xffc'

    def test_coverup_assert_length(self, tinyrom: ROM):
        tinyrom.coverup(0, 1)
        assert len(tinyrom) == 2


class TestCoveredROM(object):
    def setup(self):
        self.rom = ROM(b'abcdefghij')
        self.rom.coverup(0, 1, virtual=False)
        self.rom.coverup(4, 6, virtual=False)
        self.rom.coverup(8, 10, virtual=False)

    def test_bytes(self):
        assert bytes(self.rom) == b'bcdgh'

    def test_len(self):
        assert len(self.rom) == 5

    @pytest.mark.parametrize("index, expected", [
        (0, b'b'),
        (1, b'c'),
        (2, b'd'),
        (3, b'g'),
        (4, b'h'),
        (-5, b'b'),
        (-4, b'c'),
        (-3, b'd'),
        (-2, b'g'),
        (-1, b'h'),
    ])
    def test_getitem(self, index, expected):
        assert self.rom[index] == expected

    @pytest.mark.parametrize("index", [
        5, -6,
    ])
    def test_getitem_raises(self, index):
        with pytest.raises(IndexError):
            self.rom[index]

    @pytest.mark.parametrize("aindex, bindex, expected", [
        (0, 1, b'b'),
        (1, 2, b'c'),
        (2, 3, b'd'),
        (3, 4, b'g'),
        (4, 5, b'h'),
        (-5, -4, b'b'),
        (-4, -3, b'c'),
        (-3, -2, b'd'),
        (-2, -1, b'g'),
        (-1, None, b'h'),
    ])
    def test_getitem_slice(self, aindex, bindex, expected):
        assert self.rom[aindex:bindex] == expected


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


class TestROM256:
    @pytest.fixture(scope="module")
    def rom256(self):
        """ Test methods for a ROM consisting of every byte value """
        return ROM(bytes256)

    def test_repr(self, rom256):
        """ Call __repr__ """
        rpr = rom256.__repr__()
        repr_regex = r"<pyromhackit\.rom.ROM object at 0x(\d|\w)+>"
        assert re.search(repr_regex, rpr)

    def test_bytes(self, rom256):
        """ Bytestring representation """
        assert bytes(rom256) == bytes(range(256))

    def test_str(self, rom256):
        """ Unicode string representation """
        e = "ROM({})".format(repr(bytes256))
        assert str(rom256) == e

    @pytest.mark.parametrize("max_width, expected", [
        (-1, ValueError),
        (0, ValueError),
        (1, ValueError),
        (7, ValueError),
        (8, r"ROM(...)"),
        (14, r"ROM(...)"),
        (15, r"ROM(b'\x00'...)"),
        (18, r"ROM(b'\x00'...)"),
        (19, r"ROM(b'\x00\x01'...)"),
        (19, r"ROM(b'\x00\x01'...)"),
        (25, r"ROM(b'\x00\x01'...)"),
        (26, r"ROM(b'\x00\x01'...b'\xff')"),
    ])
    def test_str_contracted(self, rom256, max_width, expected):
        if expected is ValueError:
            with pytest.raises(ValueError) as excinfo:
                rom256.str_contracted(max_width)
        else:
            returned = rom256.str_contracted(max_width)
            assert returned == expected

    def test_len(self, rom256):
        """ Call len(...) on ROM instance """
        assert len(rom256) == 256

    def test_eq(self, rom256):
        """ Two ROMs constructed from the same bytestring are equal """
        assert rom256 == ROM(bytes(range(256)))

    def test_neq(self, rom256):
        """ ROM =/= bytestring """
        assert rom256 != bytes(range(2 ** 8))

    def test_index(self, rom256):
        """ Find bytestring in ROM """
        assert rom256.index(b'\x80') == 0x80

    @pytest.mark.parametrize("arg, expected", [
        (0, b'\x00'),
    ])
    def test_subscripting(self, rom256, arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert rom256[arg] == expected

    @pytest.mark.parametrize("arg, expected", [
        # (slice(1, 1), b''),  # mmap trouble
        (slice(None, 1), b'\x00'),
        (slice(1, 3), b'\x01\x02'),
        (slice(None, None), bytes256),
        (slice(None, 1000), bytes256),
        (slice(255, 1000), b'\xff'),
        # (slice(500, 1000), b''),  # mmap trouble
    ])
    def test_subscripting_slices(self, rom256, arg, expected):
        """ Subscripting support is isomorphic to bytestrings """
        assert rom256[arg] == expected

    @pytest.mark.parametrize("arg, expected", [
        (0, [bytes256]),
        (1, [b"\x00", b"\x01", b"\x02"]),
        (2, [b"\x00\x01", b"\x02\x03", b"\x04\x05"]),
        (3, [b"\x00\x01\x02", b"\x03\x04\x05", b"\x06\x07\x08"]),
        (255, [bytes256[:-1], b"\xff"]),
        (256, [bytes256]),
        (257, [bytes256]),
    ])
    def test_lines_first_three(self, rom256, arg, expected):
        """ Split ROM into a list """
        assert rom256.lines(arg)[:3] == expected

    @pytest.mark.parametrize("arg, expected", [
        (0, [bytes256]),
        (1, [b"\xfd", b"\xfe", b"\xff"]),
        (2, [b"\xfa\xfb", b"\xfc\xfd", b"\xfe\xff"]),
        (3, [b"\xf9\xfa\xfb", b"\xfc\xfd\xfe", b"\xff"]),
        (255, [bytes256[:-1], b"\xff"]),
        (256, [bytes256]),
        (257, [bytes256]),
    ])
    def test_lines_last_three(self, rom256, arg, expected):
        """ Split ROM into a list """
        assert rom256.lines(arg)[-3:] == expected


@pytest.mark.parametrize("expected, max_width, rombytes", [
    # (ValueError, 7, b""),  # mmap trouble
    # (r"ROM(b'')", 8, b""),  # mmap trouble
    (r"ROM(...)", 8, b"a"),
    (r"ROM(b'a')", 9, b"a"),
    (r"ROM(b'ab')", 10, b"ab"),
    (r"ROM(b'abc')", 11, b"abc"),
    (r"ROM(b'abcd')", 12, b"abcd"),
    (r"ROM(b'a'...)", 12, b"abcde"),
    (r"ROM(b'abcde')", 13, b"abcde"),
    (r"ROM(b'ab'...)", 13, b"abcdef"),
    (r"ROM(b'abcdefghi')", 17, b"abcdefghi"),
    (r"ROM(b'ab'...b'j')", 17, b"abcdefghij"),
    (r"ROM(b'abcdefghij')", 18, b"abcdefghij"),
    (r"ROM(b'abc'...b'k')", 18, b"abcdefghijk"),
    (r"ROM(...)", 9, b"\t"),
    (r"ROM(b'\t')", 10, b"\t"),
    (r"ROM(...)", 10, b"\ta"),
    (r"ROM(...)", 9, b"\xff"),
    (r"ROM(...)", 10, b"\xff"),
    (r"ROM(...)", 11, b"\xff"),
    (r"ROM(b'\xff')", 12, b"\xff"),
    (r"ROM(b'\xff')", 13, b"\xff"),
    (r"ROM(b'\xff')", 14, b"\xff"),
    (r"ROM(b'\xff')", 15, b"\xff"),
    (r"ROM(b'\xff\xfe')", 16, b"\xff\xfe"),
])
def test_str_contracted(expected, max_width, rombytes):
    rom = ROM(rombytes)
    if expected is ValueError:
        with pytest.raises(ValueError) as excinfo:
            rom.str_contracted(max_width)
    else:
        returned = rom.str_contracted(max_width)
        assert returned == expected


class TestStructuredROMFromFile:
    def test_atomcount(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"1h0o0w")
            f.flush()
            rom = ROM(f.name)
            assert rom.atomcount() == 6


class TestStructuredROM(object):
    def setup(self):
        self.rom = ROM(b'1h0o0w', structure=SimpleTopology(2))

    def test_atomcount(self):
        assert self.rom.atomcount() == 3

    @pytest.mark.parametrize("idx, expected", [
        (0, b'1h'),
        (1, b'0o'),
        (2, b'0w'),
    ])
    def test_getatom(self, idx, expected):
        assert self.rom.getatom(idx) == expected

    @pytest.mark.skip("Not sure if this method should even exist, even for debug purposes")
    def test_traverse_preorder(self):
        assert list(self.rom.traverse_preorder()) == [
            (0, 0, (0,), 0, b'1h'),
            (2, 1, (1,), 2, b'0o'),
            (4, 2, (2,), 4, b'0w'),
        ]


@pytest.mark.skip("Unsupported feature for now")
@pytest.mark.parametrize("args, expected", [
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
@pytest.mark.skip("Unsupported feature for now")
def test_pipe2(args, expected):
    rom = ROM(ROM(ROMPATH)[257:257 + 13])
    returned = rom.pipe(*args)
    assert returned == expected


def test_pipe3():
    rom = ROM(b'abc')
    returned = rom.pipe()
    assert returned == ROM(b'abc')


def remove_files():
    """ Remove leftover files """
    try:
        os.remove(OUTPATH)
    except IOError:
        pass


@pytest.fixture()
def write_rom_to_file(request):
    mode, pipeline, expected = request.param
    rom = ROM(ROM(ROMPATH)[257:257 + 13])
    rom.pipe(pipeline)
    with open(OUTPATH, mode) as outfile:
        returned = outfile.read()
        yield (mode, pipeline, returned, expected)
    remove_files()


@pytest.mark.parametrize("write_rom_to_file", [
    ("rb", "save {}".format(OUTPATH), rb"23623=3\9325<"),
    ("r", "map {} | save {}".format(MAPPATH, OUTPATH), "reprehenderit"),
], indirect=True)
@pytest.mark.skip("Unsupported feature for now")
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
    ("abcdefg", "tabulate 3 -b --padding", tables[1]),
    ("abcdefg", "tabulate 3 -b -p", tables[1]),
], indirect=True)
def test_execute(execution):
    """ Test ROM.execute(execstr) """
    returned, expected = execution
    assert returned == expected
