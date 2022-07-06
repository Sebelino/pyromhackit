from typing import Iterator

import pytest

from .finder import RotatingMonobyteFinder
from ...topology.simple_topology import SimpleTopology


class LeetDictionary:
    def __init__(self):
        self._words = frozenset(["1337"])

    def iterbytestrings(self) -> Iterator[bytes]:
        return (word.encode() for word in self._words)


@pytest.fixture
def finder():
    return RotatingMonobyteFinder(LeetDictionary())


def test_finder_rot0(finder):
    semantics = finder.find(b"y1337y")
    assert isinstance(semantics.topology, SimpleTopology)
    assert semantics.codec == {
        b"y": "y",
        b"1": "1",
        b"3": "3",
        b"7": "7",
    }


def test_finder_rot1(finder):
    semantics = finder.find(b"z2448z")
    assert semantics.codec == {
        b"z": "y",
        b"2": "1",
        b"4": "3",
        b"8": "7",
    }


def test_finder_rot255(finder):
    semantics = finder.find(b"x0226x")
    assert semantics.codec == {
        b"x": "y",
        b"0": "1",
        b"2": "3",
        b"6": "7",
    }


def test_finder_no_match(finder):
    semantics = finder.find(b"y1338y")
    assert semantics is None


def test_finder_multiple_matches(finder):
    semantics = finder.find(b"1337y2448")
    assert semantics is not None
