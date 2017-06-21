#!/usr/bin/env python

import os
import pytest

from pyromhackit.rom import ROM
from pyromhackit.morphism import Hacker
from pyromhackit.tree import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))


class TestSimpleTwoToplogy(object):
    def setup(self):
        self.topology = SimpleTopology(2)

    @pytest.mark.parametrize("arg, expected", [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 2),
        (5, 3),
    ])
    def test_length(self, arg, expected):
        assert self.topology.length(arg) == expected
