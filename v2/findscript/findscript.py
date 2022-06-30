from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    start: int
    end: int
    offset: int


class Rom:
    def __init__(self, content: bytes):
        self._content = content

    @property
    def content(self) -> bytes:
        return self._content

    def find(self, searchstring: str):
        bytestring = searchstring.encode()
        for offset in range(256):
            rot_bytestring = self._rotate(bytestring, offset)
            index = self.content.find(rot_bytestring)
            if index != -1:
                break
        else:
            raise NotImplementedError
        return SearchResult(index, index + len(bytestring), offset)

    def rotate(self, offset: int):
        rotated = self._rotate(self.content, offset)
        return Rom(rotated)

    @staticmethod
    def _rotate(bytestring: bytes, offset: int):
        return bytes([(b + offset) % 256 for b in bytestring])

    def save(self, filename: str):
        with open(filename, 'wb') as f:
            f.write(self.content)


def load(filename: str):
    with open(filename, 'rb') as f:
        content = f.read()
    return Rom(content)
