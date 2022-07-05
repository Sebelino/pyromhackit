import os
from typing import Iterator

package_dir = os.path.dirname(os.path.abspath(__file__))


class EnglishDictionary:
    def __init__(self):
        with open(os.path.join(package_dir, "../stringsearch/resources/cracklib-small-subset.txt")) as f:
            self._words = frozenset(word.strip() for word in f.read().strip().split())

    def iterbytestrings(self) -> Iterator[bytes]:
        return (word.encode() for word in self._words)
