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

            ],
        },
    }
    for strictness in negatives:
        for fmt in negatives[strictness]:
            for palette in negatives[strictness][fmt]:
                yield assert_raises, AssertionError, validate, palette, fmt, strictness

def teardown():
    pass