#!/usr/bin/env python

""" Black-box testing on the interface exposed to the average user. """

import os

import pytest

from pyromhackit.rom import ROM
from pyromhackit.morphism import Hacker
from pyromhackit.tree import SimpleTopology
from pyromhackit.roms.persona1usa.dump import tensi_path, persona_codec_path, persona_visage_path, tensi_selection_path

package_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif(not os.path.exists(tensi_path), reason="File not found")
class TestDumpAndFind:
    def setup_class(self):
        self.created_files = [os.path.join(package_dir, "tensi.txt")]

    def test_dump_tensi(self):
        rom = ROM(tensi_path, structure=SimpleTopology(2))
        hacker = Hacker(rom)
        hacker.load_codec(persona_codec_path)
        hacker.load_visage(persona_visage_path)
        #hacker.load_selection(tensi_selection_path)
        dump_path = self.created_files[0]
        hacker.dump_view(dump_path)
        assert os.path.exists(dump_path)
        included_strings = [
            "Since",
            "enthroned",
            "How charming!",
        ]
        with open(dump_path) as f:
            content = f.read()
            seek = 0
            for s in included_strings:
                idx = content.find(s, seek + 1)
                assert idx >= 0, "Script excerpt \"{}\" not found.".format(s)
                assert idx >= seek, "Script excerpt \"{}\" found in the wrong place."
                seek = idx

    def teardown(self):
        for created_file in self.created_files:
            os.remove(created_file)

@pytest.mark.skipif(not os.path.exists(tensi_path), reason="File not found")
class TestCoverup:
    def setup(self):
        self.created_files = [os.path.join(package_dir, "tensi.txt")]
        rom = ROM(tensi_path, structure=SimpleTopology(2))
        self.hacker = Hacker(rom)
        self.hacker.load_codec(persona_codec_path)
        self.hacker.load_visage(persona_visage_path)

    def test_load_selection(self):
        """ Assert that the garbage in the beginning of the file is stripped off. """
        self.hacker.load_selection(tensi_selection_path)
        assert self.hacker[0:5] == "Since"
        assert self.hacker[-8:] == "I don't."

    def teardown(self):
        for created_file in self.created_files:
            try:
                os.remove(created_file)
            except OSError:
                pass
