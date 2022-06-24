class Rom:
    def __init__(self, content: bytes):
        self._content = content

    @property
    def content(self) -> bytes:
        return self._content

    def find(self, searchstring: str):
        bytestring = searchstring.encode()
        for offset in range(256):
            rot_bytestring = bytes([b + offset for b in bytestring])
            index = self.content.find(rot_bytestring)
            if index != -1:
                break
        else:
            raise NotImplementedError
        return index, index + len(bytestring)


def load(filename: str):
    with open(filename, 'rb') as f:
        content = f.read()
    return Rom(content)
