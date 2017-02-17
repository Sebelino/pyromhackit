#!/usr/bin/env python

import os
from .dump import rom_path, Persona1Codec
from pyromhackit.rom import ROM
from pyromhackit.morphism import Morphism
import pytest

package_dir = os.path.dirname(os.path.abspath(__file__))


def test_read_rom():
    ROM(rom_path)


class TestWord(object):
    def setup_class(self):
        rom = ROM(rom_path)
        idx = 25704*2  # Index of "How"
        wordlength = 6
        rom = rom[idx:idx+wordlength]
        self.morphism = Morphism(rom, Persona1Codec)

    def test_src(self):
        assert self.morphism.src == ROM(b'\x00\xe7\x01\x0f\x01\x17')

    def test_dst(self):
        assert self.morphism.dst == 'How'

    def test_srctree(self):
        assert self.morphism.srctree == [b'\x00\xe7', b'\x01\x0f', b'\x01\x17']

    @pytest.mark.skip()
    def test_dsttree(self):
        assert self.morphism.srctree == ['H', 'o', 'w']

    @pytest.mark.parametrize("bindex, sindex", [
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 2),
    ])
    @pytest.mark.skip()
    def test_graph(self, bindex, sindex):
        assert self.morphism.graph[bindex] == sindex
