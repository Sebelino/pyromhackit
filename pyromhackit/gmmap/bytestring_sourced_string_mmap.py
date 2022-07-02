import mmap
from typing import Optional

from pyromhackit.gmmap.sourced_gmmap import SourcedGMmap
from pyromhackit.gmmap.string_mmap import StringMmap


class BytestringSourcedStringMmap(SourcedGMmap, StringMmap):
    """ A StringMmap where the source is extracted from a bytestring iterator and a codec mapping those bytestrings to
    strings. """

    def __init__(self, bytestring_iterator, codec):
        source = (codec[atom] for atom in bytestring_iterator)
        self._content, self._length = self._source2mmap(source)
        self._path = None

    @property
    def _content(self) -> mmap.mmap:
        return self._m_content

    @property
    def _path(self) -> Optional[str]:
        return self._m_path

    @property
    def _length(self) -> int:
        return self._m_length

    @_content.setter
    def _content(self, value):
        self._m_content = value

    @_length.setter
    def _length(self, value):
        self._m_length = value

    @_path.setter
    def _path(self, value):
        self._m_path = value
