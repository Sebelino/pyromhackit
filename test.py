#!/usr/bin/env python

from paletteformatter import formatconvert, validate
from nose.tools import assert_equals, assert_not_equals, assert_raises
from os.path import isfile
import os

RGB24BPPPATH = "./testsuite/sample.rgb24bpp"
RGB24BPPHEXPATH = "./testsuite/sample.rgb24bpphex"
TBLPATH = "./testsuite/sample.TBL"

def setUp():
    assert isfile(RGB24BPPPATH)

def test_validate():
    positives = {
        "nazi": {
            "rgb24bpp": [
                b"\x00\x00\x00",
                bytes([49, 23, 255]),
                bytes([49, 23, 255, 255, 255, 0]),
            ],
            "rgb24bpphex": [
                b"00 00 00",
                b"AA AA AA",
            ],
            "bgr15bpp": [
                b"\x00\x00",
                b"\x7F\xFF",
                b"\x7F\xFF\x7F\xA5",
            ],
            "tlp": [
                b"TLP\x02"+bytes([0, 0, 0, 0]*16)
            ],
            "riffpal": [
                b"RIFF"+b"\x14\0\0\0"+b"PAL data"+b"\x08\0\0\0"+b"\0\x03"+b"\x01\0"+b"\0\0\0\0",
                b'RIFF(\x00\x00\x00PAL data\x1c\x00\x00\x00\x00\x03\x06\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff\x00\x00\x00\x00\xff\x00\xff\xff\x00\x00\xff\xff\xff\x00',
            ],
        },
    }
    for strictness in positives:
        for fmt in positives[strictness]:
            for palette in positives[strictness][fmt]:
                yield validate, palette, fmt, strictness
    negatives = {
        "nazi": {
            "rgb24bpp": [
                b"",
                b"\x00",
                b"\x00\x00",
                b"\x00\x00\x00\x00",
                "\x00\x00\x00"
            ],
            "rgb24bpphex": [
                b"",
                b"00",
                b"00 11",
                b"00 11 22 33",
                b"aa aa aa",
            ],
            "bgr15bpp": [
                b"",
                b"\x7F",
                b"\x7F\xFF\x7F",
                b"\x80\x00",
            ],
        },
    }
    for strictness in negatives:
        for fmt in negatives[strictness]:
            for palette in negatives[strictness][fmt]:
                yield assert_raises, AssertionError, validate, palette, fmt, strictness

def teardown():
    pass