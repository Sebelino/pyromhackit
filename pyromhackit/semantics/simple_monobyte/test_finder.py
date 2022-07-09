import pytest

from .finder import SimpleMonobyteFinder
from ..core.test_analyzer import CACHE_PATH
from ..semantics import Semantics


@pytest.fixture
def finder():
    return SimpleMonobyteFinder(cache_path=CACHE_PATH)


def test_finder_hello(finder):
    bytestring = b"&&Hello$$$"
    semantics = finder.find(bytestring)
    assert semantics.codec.keys() == {b"&", b"$", b"H", b"e", b"l", b"o"}
    assert {
        (b"H", "H"),
        (b"e", "e"),
        (b"l", "l"),
        (b"o", "o"),
    }.issubset(semantics.codec.items())
    byteslist = semantics.topology.structure(bytestring)
    assert b"".join(byteslist) == bytestring
    stringlist = [semantics.codec[bs] for bs in byteslist]
    assert stringlist == ["&", "&", "H", "e", "l", "l", "o", "$", "$", "$"]


def test_finder_world(finder):
    bytestring = b"&&World"
    semantics = finder.find(bytestring)
    assert isinstance(semantics, Semantics)
    assert semantics.codec.keys() == {b"&", b"W", b"o", b"r", b"l", b"d"}
    assert {
        (b"W", "W"),
        (b"o", "o"),
        (b"r", "r"),
        (b"l", "l"),
        (b"d", "d"),
    }.issubset(semantics.codec.items())
    byteslist = semantics.topology.structure(bytestring)
    assert b"".join(byteslist) == bytestring
    stringlist = [semantics.codec[bs] for bs in byteslist]
    assert stringlist == ["&", "&", "W", "o", "r", "l", "d"]


def test_finder_finds_nothing(finder):
    bytestring = b".%$~,&"
    semantics = finder.find(bytestring)
    assert semantics is None
