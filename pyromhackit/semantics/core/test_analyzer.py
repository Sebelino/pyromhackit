from typing import Iterator

import pytest

from .analyzer import Analyzer
from .rot_analyzer import RotAnalyzer


class LeetDictionary:
    def __init__(self):
        self._words = frozenset(["1337"])

    def iterbytestrings(self) -> Iterator[bytes]:
        return (word.encode() for word in self._words)


@pytest.fixture
def rot_analyzer() -> RotAnalyzer:
    return RotAnalyzer(Analyzer(LeetDictionary()))


def test_all_word_frequencies(rot_analyzer):
    bytestring = b"1337hoy2448"
    freqs = rot_analyzer.all_word_frequencies(bytestring)

    assert freqs == {
        0: {b"1337": 1},
        255: {b"1337": 1},
    }
