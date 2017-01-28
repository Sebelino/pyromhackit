#!/usr/bin/env python

from .paletteformatter import (
    Strictness,
    formatconvert,
    validate,
    format2rgb24bpp,
    rgb24bpp2format
)

from nose.tools import assert_equals, assert_raises
import os

package_dir = os.path.dirname(os.path.abspath(__file__))


def setUp():
    pass


def assert_equals_bytes(returned, expected):
    retstr = ",".join("{:3}".format(c) for c in returned)
    expstr = ",".join("{:3}".format(c) for c in expected)
    msg = "Bytestrings not equal:\nbytes({})\nbytes({})".format(retstr, expstr)
    assert_equals(returned, expected, msg)


def test_validate():
    positives = {
        Strictness.pedantic: {
            "rgb24bpp": [
                b"\x00\x00\x00",
                bytes([49, 23, 255]),
                bytes([49, 23, 255, 255, 255, 0]),
            ],
            "rgb24bpphex": [
                b"00 00 00",
                b"AA AA AA",
                b"11 33 22 11 22 33",
            ],
            "bgr15bpp": [
                b"\x00\x00",
                b"\xFF\x7F",
                b"\xFF\x7F\xA5\x7F",
            ],
            "tpl": [
                b"TPL\x02"+bytes([0, 0, 0, 0]*16)
            ],
            "riffpal": [
                b"RIFF"+b"\x14\0\0\0"+b"PAL data"+b"\x08\0\0\0"+b"\0\x03"
                b"\x01\0"+b"\0\0\0\0",
                b"RIFF(\x00\x00\x00PAL data\x1c\x00\x00\x00\x00\x03\x06\x00"
                b"\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff"
                b"\x00\xff\xff\x00\x00\xff\xff\xff\x00",
            ],
        },
    }
    for strictness in positives:
        for fmt in positives[strictness]:
            for palette in positives[strictness][fmt]:
                yield validate, palette, fmt, strictness
    negatives = {
        Strictness.pedantic: {
            "rgb24bpp": [
                b"",
                b"\x00",
                b"\x00\x00",
                b"\x00\x00\x00\x00",
            ],
            "rgb24bpphex": [
                b"",
                b"00",
                b"00 11",
                b"00 11 22 33",
            ],
            "bgr15bpp": [
                b"",
                b"\x7F",
                b"\xFF\x7F\x7F",
                b"\x00\x80",
            ],
        },
        Strictness.nazi: {
            "rgb24bpphex": [
                b"aa aa aa",
                b"11 33 22 11 22 33",
                b"AA BB CC AA BB CC",
            ],
        },
    }
    for strictness in negatives:
        for fmt in negatives[strictness]:
            for palette in negatives[strictness][fmt]:
                yield assert_raises, AssertionError, validate, palette, fmt, strictness


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


def teardown():
    try:
        os.remove(os.path.join(package_dir, "./sample.dat"))
    except OSError:  # FileNotFoundError
        pass
