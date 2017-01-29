#!/usr/bin/env python

from .paletteformatter import (
    Strictness,
    formatconvert,
    validate,
    format2rgb24bpp,
    rgb24bpp2format
)

import pytest
from nose.tools import assert_equals, assert_raises
import os

package_dir = os.path.dirname(os.path.abspath(__file__))


def setup_module():
    pass


def assert_equals_bytes(returned, expected):
    retstr = ",".join("{:3}".format(c) for c in returned)
    expstr = ",".join("{:3}".format(c) for c in expected)
    msg = "Bytestrings not equal:\nbytes({})\nbytes({})".format(retstr, expstr)
    assert returned == expected, msg

@pytest.mark.parametrize("strictness, fmt, palette", [
    (Strictness.pedantic, "rgb24bpp", b"\x00\x00\x00"),
    (Strictness.pedantic, "rgb24bpp", bytes([49, 23, 255])),
    (Strictness.pedantic, "rgb24bpp", bytes([49, 23, 255, 255, 255, 0])),
    (Strictness.pedantic, "rgb24bpphex", b"00 00 00"),
    (Strictness.pedantic, "rgb24bpphex", b"AA AA AA"),
    (Strictness.pedantic, "rgb24bpphex", b"11 33 22 11 22 33"),
    (Strictness.pedantic, "bgr15bpp", b"\x00\x00"),
    (Strictness.pedantic, "bgr15bpp", b"\xFF\x7F"),
    (Strictness.pedantic, "bgr15bpp", b"\xFF\x7F\xA5\x7F"),
    (Strictness.pedantic, "tpl", b"TPL\x02"+bytes([0, 0, 0, 0]*16)),
    (Strictness.pedantic, "riffpal", b"RIFF\x14\0\0\0PAL data\x08\0\0\0"+b"\0\x03\x01\0\0\0\0\0"),
    (Strictness.pedantic, "riffpal", (b"RIFF(\x00\x00\x00PAL data\x1c\x00\x00\x00\x00\x03\x06\x00"+
                                      b"\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff"+
                                      b"\x00\xff\xff\x00\x00\xff\xff\xff\x00")),
])
def test_validate_positives(strictness, fmt, palette):
    try:
        validate(palette, fmt, strictness)
    except AssertionError as e:
        pytest.fail("validate failed because: {0}".format(e))


@pytest.mark.parametrize("strictness, fmt, palette", [
    (Strictness.pedantic, "rgb24bpp", b""),
    (Strictness.pedantic, "rgb24bpp", b"\x00"),
    (Strictness.pedantic, "rgb24bpp", b"\x00\x00"),
    (Strictness.pedantic, "rgb24bpp", b"\x00\x00\x00\x00"),
    (Strictness.pedantic, "rgb24bpphex", b""),
    (Strictness.pedantic, "rgb24bpphex", b"00"),
    (Strictness.pedantic, "rgb24bpphex", b"00 11"),
    (Strictness.pedantic, "rgb24bpphex", b"00 11 22 33"),
    (Strictness.pedantic, "bgr15bpp", b""),
    (Strictness.pedantic, "bgr15bpp", b"\x7F"),
    (Strictness.pedantic, "bgr15bpp", b"\xFF\x7F\x7F"),
    (Strictness.pedantic, "bgr15bpp", b"\x00\x80"),
    (Strictness.nazi, "rgb24bpphex", b"aa aa aa"),
    (Strictness.nazi, "rgb24bpphex", b"11 33 22 11 22 33"),
    (Strictness.nazi, "rgb24bpphex", b"AA BB CC AA BB CC"),
])
def test_validate_negatives(strictness, fmt, palette):
    with pytest.raises(AssertionError):
        validate(palette, fmt, strictness)


def test_format2rgb24bpp():
    # TODO Test cases for uppercased file extensions?
    positives = [
        ("tpl",
         b"TPL\x02"+\
         bytes([0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0]),
         bytes([0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0])),
        ("tpl",
         b"TPL\x02"+\
         bytes([
            0b00000000,0b00000001, 0b00000010,0b00000011, 0b00000100,0b00000101, 0b00000110,0b00000111,
            0b00001000,0b00001001, 0b00001010,0b00001011, 0b00001100,0b00001101, 0b00001110,0b00001111,
            0b00010000,0b00010001, 0b00010010,0b00010011, 0b00010100,0b00010101, 0b00010110,0b00010111,
            0b00011000,0b00011001, 0b00011010,0b00011011, 0b00011100,0b00011101, 0b00011110,0b00011111,
         ]),
         bytes([
            0,  64,0,              16, 192,0,             32, 64,8,              48, 192,8,
            64, 64,16,             80, 192,16,            96, 64,24,             112,192,24,
            128,64,32,             144,192,32,            160,64,40,             176,192,40,
            192,64,48,             208,192,48,            224,64,56,             240,192,56,
         ])),
    ]
    for fmt, input, expected in positives:
        returned = format2rgb24bpp(input, fmt)
        yield assert_equals_bytes, returned, expected


def test_rgb24bpp2format():
    positives = [
        ("tpl",
         bytes([0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0]),
         b"TPL\x02"+\
         bytes([0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0,   0,0])),
        ("tpl",
         bytes([
            0,  64,0,              16, 192,0,             32, 64,8,              48, 192,8,
            64, 64,16,             80, 192,16,            96, 64,24,             112,192,24,
            128,64,32,             144,192,32,            160,64,40,             176,192,40,
            192,64,48,             208,192,48,            224,64,56,             240,192,56,
         ]),
         b"TPL\x02"+\
         bytes([
            0b00000000,0b00000001, 0b00000010,0b00000011, 0b00000100,0b00000101, 0b00000110,0b00000111,
            0b00001000,0b00001001, 0b00001010,0b00001011, 0b00001100,0b00001101, 0b00001110,0b00001111,
            0b00010000,0b00010001, 0b00010010,0b00010011, 0b00010100,0b00010101, 0b00010110,0b00010111,
            0b00011000,0b00011001, 0b00011010,0b00011011, 0b00011100,0b00011101, 0b00011110,0b00011111,
         ])),
    ]
    for fmt, input, expected in positives:
        returned = rgb24bpp2format(input, fmt)
        yield assert_equals_bytes, returned, expected


def test_formatconvert_files():
    translations = [
        ("./testsuite/onlyblack", "rgb24bpp", "rgb24bpphex"),
        ("./testsuite/onlyblack", "rgb24bpphex", "rgb24bpp"),
        ("./testsuite/blackwhite", "rgb24bpp", "rgb24bpphex"),
        ("./testsuite/blackwhite", "rgb24bpphex", "rgb24bpp"),
        ("./testsuite/increasing16", "tpl", "rgb24bpp"),
        ("./testsuite/increasing16step8", "tpl", "rgb24bpp"),
    ]
    for (prefix, f1, f2) in translations:
        inpath = os.path.join(package_dir, "{}.{}".format(prefix, f1))
        outpath = os.path.join(package_dir,"{}.{}".format(prefix, f2))
        samplefile = os.path.join(package_dir, "sample.dat")
        formatconvert(inpath, f1, f2, samplefile)
        with open(samplefile, "rb") as file1, open(outpath, "rb") as file2:
            returned = file1.read()
            expected = file2.read()
            yield assert_equals, returned.strip(), expected.strip()
            remove_files()


def remove_files():
    try:
        os.remove(os.path.join(package_dir, "./sample.dat"))
    except OSError:  # FileNotFoundError
        pass
