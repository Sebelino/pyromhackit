import pytest

from .finder import SimpleMonobyteFinder, SemanticsNotFoundException
from ..semantics import Semantics


def test_finder_hello():
    finder = SimpleMonobyteFinder()
    bytestring = b"&&Hello$$$"
    search_result = finder.find(bytestring)
    assert len(search_result.semantics_set) == 1
    semantics, = search_result.semantics_set
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


def test_finder_world():
    finder = SimpleMonobyteFinder()
    bytestring = b"&&World"
    result = finder.find(bytestring)
    assert len(result.semantics_set) == 1
    semantics, = result.semantics_set
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


def test_finder_finds_nothing():
    finder = SimpleMonobyteFinder()
    bytestring = b".%$~,&"
    with pytest.raises(SemanticsNotFoundException):
        finder.find(bytestring)
