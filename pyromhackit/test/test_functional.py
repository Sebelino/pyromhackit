#!/usr/bin/env python

""" Test suite for ROM class. """

import os

import pytest

from ..rom import Morphism
from ..roms.persona1usa.dump import Persona1Codec, rom_path

package_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif(not os.path.exists(rom_path), reason="File not found")
@pytest.mark.skip("TODO")
class TestPersona1USA:

    def test_dump_tensi(self):
        morphism = Morphism(rom_path, Persona1Codec)
        dump_path = os.path.join(package_dir, "tensi.txt")
        morphism.dump(dump_path)
        assert os.path.exists(dump_path)
        included_strings = [
            "Since you require",
            "entity is enthroned",
            "How charming! You have definite charisma.\nIt is a truly wondrous thing!",
        ]
        with open(dump_path) as f:
            content = f.read()
            seek = 0
            for s in included_strings:
                idx = content.find(s, seek + 1)
                assert idx >= 0, "Script excerpt \"{}\" not found.".format(s)
                assert idx >= seek, "Script excerpt \"{}\" found in the wrong place."
                seek = idx