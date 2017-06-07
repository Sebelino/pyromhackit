#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM
from pyromhackit.morphism import IROM
from pyromhackit.tree import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))

rom = ROM(b'\x00\xe7\x01\x0f\x01\x17', structure=SimpleTopology('2'))


def init():
    IROM(rom)


def test_str():
    irom = IROM(rom)
    assert len(str(irom)) == 3  # Actual content of string representation is undefined, but its length is known


class TestTinyIROM(object):
    def setup(self):
        self.irom = IROM(rom)
        self.irom.place(0, 'How')

    def test_setitem(self):
        self.irom[0] = 'c'
        assert str(self.irom) == 'cow'
        assert self.irom.codec[b'\x00\xe7'] == 'c'
