#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM
from pyromhackit.irom import IROM
from pyromhackit.topology.tree import SimpleTopology

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

class Test_removals_from_copy(object):
    @pytest.fixture(scope="function")
    def two_line_content(self):
        return """
hello
world
        """.strip()

    @pytest.fixture(scope="function")
    def four_line_content(self):
        return """
HelloREEE
YOOO
HEY
AAWorld
        """.strip()

    @pytest.fixture(scope="function")
    def two_chunks(self):
        return """
hello
Nodiff
HelloREEE
YOOO
HEY
AAWorld
        """.strip()

    def test_identical(self, two_line_content):
        edited_content = """
hello
world
        """.strip()
        removal = IROM.removals_from_copy(two_line_content, edited_content)
        assert len(removal) == 0

    def test_one_char_missing(self, two_line_content):
        edited_content = """
hell
world
        """.strip()
        removal = IROM.removals_from_copy(two_line_content, edited_content)
        assert list(removal) == [(4, 5)]

    def test_lines_missing(self, four_line_content):
        edited_content = """
Hello
World
        """.strip()
        removal = IROM.removals_from_copy(four_line_content, edited_content)
        assert list(removal) == [
            (5, 9),  # REEE
            (10, 21),  # YOOO\nHEY\nAA
        ]

    def test_two_chunks(self, two_chunks):
        edited_content = """
hell
Nodiff
Hello
World
        """.strip()
        removal = IROM.removals_from_copy(two_chunks, edited_content)
        assert list(removal) == [
            (4, 5),  # o
            (18, 22), # REEE
            (23, 34), # YOOO\nHEY\nAA
        ]
