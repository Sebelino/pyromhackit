import io
import mmap
from typing import Optional

from pyromhackit.gmmap.bytes_gmmap import BytesMmap
from pyromhackit.gmmap.sourced_gmmap import SourcedGMmap


class FixedWidthBytesMmap(SourcedGMmap, BytesMmap):
    """ A SourcedGMmap which is a sequence of bytestrings where all bytestrings share the same (positive)
    length. """

    def __init__(self, width, source):
        self.width = width
        self._content, self._length = self._source2mmap(source)
        if self._length is None:
            self._length = len(self._content) // width
        if isinstance(source, io.TextIOWrapper):
            self._path = source.name
        else:
            self._path = None

    @property
    def _path(self) -> Optional[str]:
        return self._m_path

    @_path.setter
    def _path(self, value: Optional[str]):
        self._m_path = value

    @property
    def _content(self) -> mmap.mmap:
        return self._m_content

    @_content.setter
    def _content(self, value: mmap.mmap):
        self._m_content = value

    @property
    def _length(self) -> int:
        return self._m_length

    @_length.setter
    def _length(self, value: int):
        self._m_length = value

    def _args2source(*args):
        width, source = args
        is_file = isinstance(source, io.TextIOWrapper)  # Quite tight but the price was right
        if not is_file:
            try:
                element = next(iter(source))
                is_bytes_iterable = isinstance(element, bytes)
            except StopIteration:
                is_bytes_iterable = True
            except TypeError:
                is_bytes_iterable = False
            assert is_bytes_iterable, \
                "Source is neither a path to an existing file nor an iterable for bytestrings: {}".format(source)
        return source

    def _logicalint2physical_unsafe(self, location: int):
        assert isinstance(location, int)  # TODO remove
        if 0 <= location < len(self):
            return slice(self.width * location, self.width * (location + 1))
        elif -len(self) <= location < -1:
            return slice(self.width * location, self.width * (location + 1))
        elif location == -1:
            return slice(self.width * location, None)

    def _logicalslice2physical(self, location: slice):
        assert isinstance(location, slice)  # TODO remove
        return slice(
            self.width * location.start if location.start else None,
            self.width * location.stop if location.stop else None,
            self.width * location.step if location.step else None,
        )
