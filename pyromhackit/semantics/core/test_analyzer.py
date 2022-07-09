from typing import Iterator

import pytest

from .analyzer import Analyzer


class LeetDictionary:
    def __init__(self):
        self._words = frozenset(["1337"])

    def iterbytestrings(self) -> Iterator[bytes]:
        return (word.encode() for word in self._words)


@pytest.fixture
def analyzer() -> Analyzer:
    return Analyzer(LeetDictionary(), path="/tmp/pyromhackit_word_frequency.test.json")


def test_count_matches(analyzer):
    assert 1 == Analyzer.count_matches(b"1337", b"1337hoy2448")


def test_word_frequency(analyzer):
    bytestring = b"1337hoy1337"
    freqs = analyzer.word_frequency(bytestring)

    assert freqs == {
        b"1337": 2,
    }
