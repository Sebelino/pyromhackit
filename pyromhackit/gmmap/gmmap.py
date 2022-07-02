import io
from abc import ABCMeta, abstractmethod

import mmap
from typing import Optional, Union

from pyromhackit.gmmap.listlike_gmmap import ListlikeGMmap
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


class PhysicallyIndexedGMmap(GMmap, metaclass=ABCMeta):
    """ GMmap where each physical location that a logical location translates into is either a slice or a Selection. """

    def _physical2bytes(self, physicallocation: Union[slice, Selection], content: mmap.mmap) -> bytes:
        """ :return The bytestring obtained when accessing the @content mmap using @physicallocation. """
        if isinstance(physicallocation, slice):
            return content[physicallocation]
        elif isinstance(physicallocation, Selection):
            return physicallocation.select(content)
        raise TypeError


class Additive(metaclass=ABCMeta):
    @abstractmethod
    def __add__(self, operand):
        return NotImplementedError()

    @abstractmethod
    def __radd__(self, operand):
        return NotImplementedError()


class BytesMmap(Additive, ListlikeGMmap, PhysicallyIndexedGMmap, metaclass=ABCMeta):
    """ A ListlikeGMmap where each element in the sequence is a bytestring of any positive length. """

    @classmethod
    def _decode(cls, bytestring: bytes):
        return bytestring

    @classmethod
    def _encode(cls, element) -> bytes:
        return element

    def __bytes__(self) -> bytes:  # Final
        """ :return The concatenation of all elements in the sequence. """
        return self[:]

    def iterbytes(self):
        """ :return A generator for every byte in every element in the sequence, left to right. """
        for bs in self:
            for b in bs:
                yield b

    def bytecount(self):
        """ :return The total number of bytes in this sequence. """
        return len(self._content)  # Assumes that self[:] == bytes(mmap)

    def __add__(self, operand: bytes) -> bytes:
        """ :return A bytestring being the concatenation of the sequence's bytestring representation and @operand. """
        return bytes(self) + operand

    def __radd__(self, operand: bytes) -> bytes:
        """ :return A bytestring being the concatenation of @operand and the sequence's bytestring representation. """
        return operand + bytes(self)


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


class SelectiveGMmap(ListlikeGMmap, PhysicallyIndexedGMmap, metaclass=ABCMeta):
    """ A ListlikeGMmap in which elements in the sequence can be marked/unmarked as being hidden from the user's
    purview. If the ith element is visible and becomes preceded by n hidden elements, that means that this element will
    henceforth be considered to be the (i-n)th element. """

    @property
    @abstractmethod
    def selection(self) -> Selection:
        raise NotImplementedError

    def _logicalint2physical(self, vindex: int):  # Final
        nonvindex = self.selection.virtual2physical(vindex)
        return self._nonvirtualint2physical(nonvindex)

    def _logicalslice2physical(self, vslice: slice):  # Final
        nonvselection = self.selection.virtual2physicalselection(vslice)
        return self._nonvirtualselection2physical(nonvselection)

    @abstractmethod
    def _nonvirtualint2physical(self, location: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def _nonvirtualselection2physical(self, location: Selection) -> Selection:
        raise NotImplementedError

    def coverup(self, from_index, to_index):
        """ Let N denote the total number of elements in the sequence. This method causes every element with index i,
        where @from_index <= i < @to_index, to become hidden (if it is not already). """
        covered_count = self.selection.exclude(from_index, to_index)
        self._length -= covered_count

    def coverup_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index I_i, where @from_index <= i < @to_index, to become hidden. """
        covered_count = self.selection.exclude_virtual(from_index, to_index)
        self._length -= covered_count

    def uncover(self, from_index, to_index):
        """ Let N denote the total number of elements in the sequence. This method causes every element with index i,
        where @from_index <= i < @to_index, to become visible (if it is not already). """
        revealed_count = self.selection.include(from_index, to_index)
        self._length += revealed_count

    def uncover_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index i, where I_@from_index < i < I_@to_index, to become visible. If @from_index is None,
        and @to_index is not None, the condition becomes i < I_@to_index. If @from_index is not None and @to_index is
        None, the condition becomes I_@from_index < i. If both are None, all elements in the sequence become visible.
        """
        revealed_count = self.selection.include(from_index, to_index)
        self._length += revealed_count


class SelectiveFixedWidthBytesMmap(SelectiveGMmap, FixedWidthBytesMmap):
    def __init__(self, width, source):
        super(SelectiveFixedWidthBytesMmap, self).__init__(width, source)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int):
        return slice(self.width * location, self.width * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection):
        return location * self.width


class SingletonBytesMmap(BytesMmap):
    """ The most useless subclass. Sequence containing a single bytestring element. """

    def _logicalint2physical_unsafe(self, location: int) -> slice:
        if location == 0:
            return slice(None, None)

    def _logicalslice2physical(self, location: slice) -> slice:
        if (location.start is None or location.start <= 0) and (location.stop is None or location.stop >= 1):
            return location
        return slice(0, 0)  # Empty slice


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
