#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM, IROM
from pyromhackit.tree import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))


def test_init():
    rom = ROM(b'1h0o0w', SimpleTopology(2))
    codec = {
        b'1h': 'H',
        b'0o': 'o',
        b'0w': 'w',
    }
    IROM(rom, codec)


class TestIROM(object):
    def setup(self):
        rom = ROM(b'1h0o0w', SimpleTopology(2))
        codec = {
            b'1h': 'H',
            b'0o': 'o',
            b'0w': 'w',
        }
        self.irom = IROM(rom, codec)

    def test_len(self):
        assert len(self.irom) == 3

    def test_str(self):
        assert str(self.irom) == 'How'

    def test_index_raises(self):
        with pytest.raises(IndexError):
            self.irom[3]
