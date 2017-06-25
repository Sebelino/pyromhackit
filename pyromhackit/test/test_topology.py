#!/usr/bin/env python

import os
import pytest

from pyromhackit.tree import SimpleTopology

package_dir = os.path.dirname(os.path.abspath(__file__))


class TestSimpleTwoTopology(object):
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

    @pytest.mark.parametrize("arg, expected", [
        (b'', []),
        (b'ab', [(0, 0, (0,), b'ab')]),
        (b'abcd', [(0, 0, (0,), b'ab'), (2, 1, (1,), b'cd')]),
    ])
    def test_traverse_preorder(self, arg, expected):
        assert list(self.topology.traverse_preorder(arg)) == expected
