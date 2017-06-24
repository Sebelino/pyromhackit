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

    @pytest.mark.skip(reason="Decide on a semantics for this (i.e. propagate changes to codec or ROM?)")
    def test_setitem(self):
        self.hacker[0] = 'c'
        assert str(self.hacker)[0] == 'c'
        assert self.hacker.codec[b'\x00\xe7'] == 'c'
