class Rom:
    def __init__(self, content: bytes):
        self._content = content

    @property
    def content(self) -> bytes:
        return self._content

    def find(self, searchstring: str):
        bytestring = searchstring.encode()
        index = self.content.find(bytestring)
        if index == -1:
            raise NotImplementedError
        return index, index + len(bytestring)


def load(filename: str):
    with open(filename, 'rb') as f:
        content = f.read()
    return Rom(content)
