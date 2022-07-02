#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM
from pyromhackit.hacker import Hacker
from pyromhackit.topology.tree import SimpleTopology
from pyromhackit.gslice.selection import Selection

package_dir = os.path.dirname(os.path.abspath(__file__))

bytestring = b'\x00\xe7\x01\x0f\x01\x17'


def test_init():
    Hacker(ROM(bytestring, structure=SimpleTopology(2)))


def test_str():
    hacker = Hacker(ROM(bytestring, structure=SimpleTopology(2)))
    assert len(str(hacker)) == 3  # Actual content of string representation is undefined, but its length is known


class TestTinyHacker(object):
    def setup(self):
        self.hacker = Hacker(ROM(bytestring, structure=SimpleTopology(2)))

    @pytest.mark.skip("Not sure if this method should even exist, even for debug purposes")
    def test_traverse_preorder(self):
        assert len(list(self.hacker.traverse_preorder())) == 3
        expected = [
            (0, 0, (0,), 0, b'\x00\xe7', 0, 0, (0,), 4),
            (2, 1, (1,), 2, b'\x01\x0f', 1, 1, (1,), 8),
            (4, 2, (2,), 4, b'\x01\x17', 2, 2, (2,), 12),
        ]
        for entry, expected_entry in zip(list(self.hacker.traverse_preorder()), expected):
            assert len(entry[:-1]) == len(expected_entry)
            assert entry[:-1] == expected_entry
            assert isinstance(entry[-1], str)

    def test_set_destination_at(self):
        self.hacker.set_destination_at(0, 'H')
        assert str(self.hacker)[0] == 'H'
        assert self.hacker.codec[b'\x00\xe7'] == 'H'

    def test_place(self):
        self.hacker.place(0, 'How')
        assert str(self.hacker) == 'How'
        assert self.hacker.codec[b'\x00\xe7'] == 'H'
        assert self.hacker.codec[b'\x01\x0f'] == 'o'
        assert self.hacker.codec[b'\x01\x17'] == 'w'

    def test_place_twice(self):
        self.hacker.place(0, 'How')
        self.hacker.place(0, 'hey')
        assert str(self.hacker) == 'hey'
        assert self.hacker.codec[b'\x00\xe7'] == 'h'
        assert self.hacker.codec[b'\x01\x0f'] == 'e'
        assert self.hacker.codec[b'\x01\x17'] == 'y'

    def test_load_selection__file_does_not_exist__selection_unchanged(self):
        try:
            self.hacker.load_selection('any_file_that_shouldnt_exist')
        except FileNotFoundError:
            pass
        assert self.hacker.dst.selection() == Selection(universe=slice(0, 3), revealed=[slice(0, 3)])

    @pytest.mark.skip(reason="Decide on a semantics for this (i.e. propagate changes to codec or ROM?)")
    def test_setitem(self):
        self.hacker[0] = 'c'
        assert str(self.hacker)[0] == 'c'
        assert self.hacker.codec[b'\x00\xe7'] == 'c'

    def test_len(self):
        return len(self.hacker) == 3

    def test_coverup(self):
        self.hacker.place(0, 'How')
        self.hacker.coverup(0, 1)
        assert bytes(self.hacker.src) == b'\x01\x0f\x01\x17'
        assert str(self.hacker.dst) == 'ow'

    def test_cover_cumulatively(self):
        self.hacker.place(0, 'How')
        self.hacker.coverup(0, 1)
        self.hacker.coverup(0, 1)
        assert bytes(self.hacker.src) == b'\x01\x17'
        assert str(self.hacker.dst) == 'w'

    def test_cover_and_edit_codec(self):
        self.hacker[0] = 'H'
        self.hacker.coverup(0, 1)
        self.hacker['H'] = 'C'
        assert len(self.hacker.src) == len(self.hacker.dst)
