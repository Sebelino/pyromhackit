#!/usr/bin/env python

import os
from pyromhackit.rom import ROM
from pyromhackit.hacker import Hacker
from pyromhackit.thousandcurses.codec import Tree
import pytest

from pyromhackit.roms.persona1usa.dump import sources

package_dir = os.path.dirname(os.path.abspath(__file__))

tensi_path, = [key for key in sources if '/TENSI.BIN' in key]


@pytest.mark.skipif(not os.path.isfile(os.path.join(package_dir, tensi_path)), reason="Copyright infringement")
def test_read_rom():
    ROM(os.path.join(package_dir, tensi_path))


@pytest.mark.skipif(not os.path.isfile(os.path.join(package_dir, tensi_path)), reason="Copyright infringement")
@pytest.mark.skip()
class TestWord(object):
    def setup_class(self):
        rom = ROM(os.path.join(package_dir, tensi_path))
        idx = 25704 * 2  # Index of "How"
        wordlength = 6
        rom = rom[idx:idx + wordlength]
        self.irom = Hacker(rom)

    def test_src(self):
        assert self.irom.src == ROM(b'\x00\xe7\x01\x0f\x01\x17')

    def test_dst(self):
        assert self.morphism.dst == 'How'

    def test_srctree(self):
        assert self.morphism.srctree == Tree([b'\x00\xe7', b'\x01\x0f', b'\x01\x17'])

    def test_dsttree(self):
        assert self.morphism.dsttree == Tree(['H', 'o', 'w'])

    @pytest.mark.parametrize("srcindex, expected_dstindices", [
        (0, {0}),
        (1, {0}),
        (2, {1}),
        (3, {1}),
        (4, {2}),
        (5, {2}),
    ])
    def test_source_diffusion(self, srcindex, expected_dstindices):
        assert self.morphism.source_diffusion(srcindex) == expected_dstindices

    @pytest.mark.parametrize("bindexpath, sindexpath", [
        ((0,), (0,)),
        ((1,), (1,)),
        ((2,), (2,)),
    ])
    def test_graph(self, bindexpath, sindexpath):
        assert self.morphism.graph[bindexpath] == sindexpath

# Dump E0.txt, ..., E4.txt
