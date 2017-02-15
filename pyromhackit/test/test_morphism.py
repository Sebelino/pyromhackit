#!/usr/bin/env python

""" Test suite for ROM class. """

import os
import re
import pytest

from ..morphism import Morphism
from ..thousandcurses.codec import ASCII

package_dir = os.path.dirname(os.path.abspath(__file__))


class TestASCIIMorphism:
    def setup(self):
        self.morphism = Morphism(b"abcdefghi", ASCII)

    def test_repr(self):
        rpr = self.morphism.__repr__()
        repr_regex = r"<pyromhackit\.morphism.Morphism object at 0x(\d|\w)+>"
        assert re.search(repr_regex, rpr)

    def test_str(self):
        expected = ("Morphism(b'abcdefghi',\n"
                    "          'abcdefghi')")
        assert str(self.morphism) == expected

    @pytest.mark.parametrize("searchitem, expected", [
        ("", (0, 0)),
        ("a", (0, 0)),
        ("abcdefghi", (0, 0)),
        ("bcdefghi", (1, 1)),
        ("fgh", (5, 5)),
    ])
    def test_index(self, searchitem, expected):
        returned = self.morphism.index(searchitem)
        assert returned == expected

    @pytest.mark.parametrize("srcindex, expected", [
        (0, {0}),
        (1, {1}),
        (8, {8}),
    ])
    def test_source_diffusion(self, srcindex, expected):
        assert self.morphism.source_diffusion(srcindex) == expected

    @pytest.mark.parametrize("byteidx, stridx, c, expected", [
        (0, 0, 'K', ord('K')),
        (0, 1, 'K', None),
        (8, 8, 'a', ord('a')),
        (0, 0, 'ä', None),
    ])
    @pytest.mark.skip()
    def test_impose_character(self, byteidx, stridx, c, expected):
        if expected is None:
            assert self.morphism.impose_character(byteidx, stridx, c) is None
        else:
            returned = self.morphism.impose_character(byteidx, stridx, c)
            msg = "Could not find a value of r[{}] so that s[{}] == {}".format(byteidx, stridx, repr(c))
            assert isinstance(returned, int), msg
            assert returned == expected

    @pytest.mark.skip("TODO (?)")
    def test_impose_decoding(self):
        newdecoder = self.morphism.impose_decoding(97, 'b')
        assert newdecoder
