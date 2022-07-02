from abc import ABCMeta, abstractmethod

import mmap
from typing import Optional

from pyromhackit.gmmap.additive import Additive
from pyromhackit.gmmap.listlike_gmmap import ListlikeGMmap
from pyromhackit.gmmap.physically_indexed_gmmap import PhysicallyIndexedGMmap
from pyromhackit.gmmap.selective_gmmap import SelectiveGMmap
from pyromhackit.gmmap.sourced_gmmap import SourcedGMmap
from pyromhackit.gslice.selection import Selection


class GMmap(metaclass=ABCMeta):
    """ Generalized mmap. While a regular mmap stores a non-empty sequence of bytes, a GMmap stores a potentially empty
    sequence of elements of any type(s) satisfying the following conditions:
    * The bytestring representation of a sequence equals the concatenation of the individual elements' bytestring
      representations.
    * For any instance of a deriving class, the bytestring representation of an element cannot change during the
    instance's lifetime.
    * The sequence has a defined length given by __len__.
    * The elements of the sequence are accessed using __getitem__. The type(s) of the objects used as the argument is up
      to the deriving class.
    """

    @property
    @abstractmethod
    def _content(self) -> mmap.mmap:
        """ :return The underlying mmap storing the sequence as a byte buffer. """
        raise NotImplementedError

    @_content.setter
    @abstractmethod
    def _content(self, value: mmap.mmap):
        raise NotImplementedError

    @property
    @abstractmethod
    def _length(self) -> int:
        """ :return The number of elements in the sequence. """
        raise NotImplementedError

    @_length.setter
    @abstractmethod
    def _length(self, value: int):
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _encode(cls, element) -> bytes:
        """ :return The bytestring that @element encodes into. """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def _decode(cls, bytestring: bytes):
        """ :return The element that @bytestring encodes. """
        raise NotImplementedError()

    """ Post-initialization methods -- may only be called after __init__ finishes """

    @abstractmethod
    def _logical2physical(self, location):
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence.
        :raise IndexError if @location is out of bounds. """
        raise NotImplementedError()

    @abstractmethod
    def _physical2bytes(self, physicallocation, content: mmap.mmap) -> bytes:
        """ :return The bytestring obtained when accessing the @content mmap using @physicallocation. """
        raise NotImplementedError

    def __getitem__(self, location):  # Final
        """ :return A sub-sequence that @location refers to. """
        bytestringlocation = self._logical2physical(location)
        bytestringrepr = self._physical2bytes(bytestringlocation, self._content)
        value = self._decode(bytestringrepr)
        return value

    def __len__(self):  # Final
        """ :return The number of elements in the sequence. """
        return self._length


class StringMmap(Additive, ListlikeGMmap, PhysicallyIndexedGMmap, metaclass=ABCMeta):
    """ A ListlikeGMmap where each element in the sequence is a Unicode string of any positive length. """

    def _logicalslice2physical(self, location: slice) -> slice:
        return slice(
            4 * location.start if location.start else None,
            4 * location.stop if location.stop else None,
            4 * location.step if location.step else None,
        )

    def _logicalint2physical_unsafe(self, location: int) -> slice:
        if 0 <= location < len(self):
            return slice(4 * location, 4 * (location + 1))
        elif -len(self) <= location < -1:
            return slice(4 * location, 4 * (location + 1))
        elif location == -1:
            return slice(4 * location, None)

    @classmethod
    def _encode(cls, element: str) -> bytes:
        return element.encode('utf-32')[4:]

    @classmethod
    def _decode(cls, bytestring: bytes) -> str:
        prefix = ''.encode('utf-32')
        return (prefix + bytestring).decode('utf-32')

    def __add__(self, operand: str) -> str:
        """ :return A string being the concatenation of the sequence's string representation and @operand. """
        return str(self) + operand

    def __radd__(self, operand: str) -> str:
        """ :return A string being the concatenation of @operand and the sequence's string representation. """
        return operand + str(self)


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


class SelectiveBytestringSourcedStringMmap(SelectiveGMmap, BytestringSourcedStringMmap):

    def __init__(self, bytestring_iterator, codec):
        super(SelectiveBytestringSourcedStringMmap, self).__init__(bytestring_iterator, codec)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int) -> slice:
        return slice(4 * location, 4 * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection) -> Selection:
        return location * 4
