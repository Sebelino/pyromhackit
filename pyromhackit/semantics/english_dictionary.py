from typing import Iterator


class EnglishDictionary:
    def __init__(self):
        with open("pyromhackit/stringsearch/resources/cracklib-small-subset.txt") as f:
            self._words = frozenset(word.strip() for word in f.read().strip().split())

    def iterbytestrings(self) -> Iterator[bytes]:
        return (word.encode() for word in self._words)
