import io
import mmap
from abc import ABCMeta, abstractmethod
from typing import Optional

from pyromhackit.gmmap.gmmap import GMmap


class SourcedGMmap(GMmap, metaclass=ABCMeta):
    """
    GMmap whose content originates from either an iterable storing the elements of the sequence, or a file.
    """

    @property
    @abstractmethod
    def _path(self) -> Optional[str]:
        raise NotImplementedError

    @_path.setter
    @abstractmethod
    def _path(self, value: Optional[str]):
        raise NotImplementedError

    @property
    def path(self) -> Optional[str]:
        return self._path

    @classmethod
    def _source2triple(cls, source):
        if isinstance(source, io.TextIOWrapper):  # Source is file
            content = cls._file2mmap(source)
            path = source.name
            length = cls._initial_length(content)
        else:
            content = cls._sequence2mmap(source)
            path = None
            length = cls._initial_length(content)  # Cannot do len(source) if it is a generator
        return content, length, path

    @classmethod
    def _source2mmap(cls, source) -> (mmap.mmap, int):
        if isinstance(source, io.TextIOWrapper):  # Source is file
            return cls._file2mmap(source), None  # FIXME
        else:
            return cls._sequence2mmap(source)

    @classmethod
    def _sequence2mmap(cls, sequence) -> (mmap.mmap, int):  # Final
        """ :return An anonymous mmap storing the bytestring representation of the sequence @sequence, paired with the
        number of elements in the sequence. @sequence needs to either be a bytestring or an iterable containing only
        elements that implement __len__. """

        def double_mmap_capacity(m):
            new_m = mmap.mmap(-1, capacity)
            new_m.write(bytes(m))  # FIXME Potentially large bytestring
            m.close()
            return new_m

        protection = cls._access()
        if isinstance(sequence, bytes):
            m = mmap.mmap(-1, len(sequence), access=protection)
            m.write(sequence)
            return m, len(m)
        capacity = mmap.PAGESIZE  # Initial capacity. Cannot do len(sequence) since it is a generator.
        m = mmap.mmap(-1, capacity)
        currentsize = 0
        element_count = 0
        for element in sequence:
            element_count += 1
            bs = cls._encode(element)
            currentsize += len(bs)
            while currentsize > capacity:
                capacity *= 2
                m = double_mmap_capacity(m)  # Because m.resize() is apparently bugged and causes SIGBUS
            m.write(bs)
        m.resize(currentsize)
        return m, element_count

    @classmethod
    def _file2mmap(cls, file) -> mmap.mmap:  # Final
        """ :return A mmap storing the bytestring representation of the sequence originating from the file @file. """
        protection = cls._access()
        m = mmap.mmap(file.fileno(), 0, access=protection)
        return m

    @staticmethod
    def _access():
        """ :return The memory protection of the memory-mapped file. By default, readable and writable. """
        return mmap.ACCESS_READ | mmap.ACCESS_WRITE
