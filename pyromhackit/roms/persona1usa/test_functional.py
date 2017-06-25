#!/usr/bin/env python

""" Black-box testing on the interface exposed to the average user. """

import os

import pytest

from pyromhackit.rom import ROM
from pyromhackit.morphism import Hacker
from pyromhackit.tree import SimpleTopology
from pyromhackit.roms.persona1usa.dump import tensi_path, persona_codec_path, persona_visage_path

package_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif(not os.path.exists(tensi_path), reason="File not found")
class TestPersona1USA:

    def test_dump_tensi(self):
        rom = ROM(tensi_path, structure=SimpleTopology(2))
        hacker = Hacker(rom)
        print("DEBUG HACKER DONE")
        hacker.load_codec(persona_codec_path)
        print("DEBUG HACKER CODEC LOADED")
        hacker.load_visage(persona_visage_path)
        print("DEBUG HACKER VISAGE LOADED")
        print(hacker)
        dump_path = os.path.join(package_dir, "tensi.txt")
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
