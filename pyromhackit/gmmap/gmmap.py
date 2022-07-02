from abc import ABCMeta, abstractmethod

import mmap
from typing import Optional

from pyromhackit.gmmap.selective_gmmap import SelectiveGMmap
from pyromhackit.gmmap.sourced_gmmap import SourcedGMmap
from pyromhackit.gmmap.string_mmap import StringMmap
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
