#!/usr/bin/env python

""" Test suite for ROM class. """

import os

from ..rom import Morphism
from ..thousandcurses.codec import ASCII

package_dir = os.path.dirname(os.path.abspath(__file__))


class TestASCIIMorphism:
    def setup_class(self):
        self.morphism = Morphism(b"abcdefghi", ASCII)

    def test_repr(self):
        expected = "Morphism(b'abcdefghi', 'abcdefghi')"
        assert repr(self.morphism) == expected

    def test_str(self):
        expected = ("Morphism(b'abcdefghi',\n"
                    "          'abcdefghi')")
        assert str(self.morphism) == expected
