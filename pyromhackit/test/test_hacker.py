#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM
from pyromhackit.morphism import Hacker
from pyromhackit.tree import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))

rom = ROM(b'\x00\xe7\x01\x0f\x01\x17', structure=SimpleTopology(2))


def test_init():
    Hacker(rom)


def test_str():
    hacker = Hacker(rom)
    assert len(str(hacker)) == 3  # Actual content of string representation is undefined, but its length is known


class TestTinyHacker(object):
    def setup(self):
        self.hacker = Hacker(rom)
        self.hacker.place(0, 'How')

    def test_setitem(self):
        self.hacker[0] = 'c'
        assert str(self.hacker) == 'cow'
        assert self.hacker.codec[b'\x00\xe7'] == 'c'
