import io
from abc import ABCMeta, abstractmethod

import mmap
from typing import Optional, Union

import itertools

from pyromhackit.selection import Selection


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


class SettableGMmap(GMmap, metaclass=ABCMeta):
    def __setitem__(self, location, val):  # Final
        """ Sets the @location'th element to @val, if @location is an integer; or sets the sub-sequence retrieved when
        slicing the sequence with @location to @val, if @location is a slice. """
        bytestringrepr = self._encode(val)
        bytestringlocation = self._logical2physical(location)
        self._content[bytestringlocation] = bytestringrepr


class DeletableGMmap(GMmap, metaclass=ABCMeta):
    @abstractmethod  # Can this be non-abstract? Hmm...
    def __delitem__(self, location):  # Final
        """ Removes the @location'th element, if @location is an integer; or the sub-sequence retrieved when slicing the
        sequence with @location, if @location is a slice. """
        raise NotImplementedError()


class IndexedGMmap(GMmap, metaclass=ABCMeta):
    """ GMmap where the indices used to access elements in the sequence are either integers or slices. """

    def _logical2physical(self, location: Union[int, slice]):
        """ :return The location of the bytestring that encodes the element(s) at location @location of the sequence.
        :raise IndexError if @location is an integer and is out of bounds. """
        if isinstance(location, int):
            return self._logicalint2physical(location)
        elif isinstance(location, slice):
            return self._logicalslice2physical(location)
        else:
            raise TypeError("Unexpected location type: {}".format(type(location)))

    @abstractmethod
    def _logicalint2physical_unsafe(self, location: int):
        """ :return The slice for the bytestring that encodes the element(s) at integer index @location of the sequence.
        The behavior is undefined if @location is out of bounds. """
        raise NotImplementedError()

    def _logicalint2physical(self, location: int):  # Final
        """ :return The slice for the bytestring that encodes the element(s) at integer index @location of the sequence.
        :raise IndexError if @location is out of bounds. """
        if self._is_within_bounds(location):
            return self._logicalint2physical_unsafe(location)
        raise IndexError("Index out of bounds: {}".format(location))

    @abstractmethod
    def _is_within_bounds(self, location: int):
        """ :return True iff accessing this GMmap by index @location yields an element in the sequence. """
        raise NotImplementedError

    @abstractmethod
    def _logicalslice2physical(self, location: slice):
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence. """
        raise NotImplementedError()


class ListlikeGMmap(IndexedGMmap, metaclass=ABCMeta):
    """ IndexedGMmap where
    * using an integer i as index yields the ith element in the sequence
    * using a slice(i, j) as index yields a the subsequence (a_i, a_(i+1), ..., a_j) where a is the sequence
    * negative integers are interpreted as counting from the end of the list.
    """

    def _is_within_bounds(self, location: int):
        """ :return True iff accessing this GMmap by index @location yields an element in the sequence. """
        return -len(self) <= location < len(self)

    def _recompute_length(self):
        """ :return The length of the sequence which is computed in O(n*log(n)) by finding the lowest non-negative index
        that raises an IndexError. """
        try:
            self._logicalint2physical(0)
        except IndexError:
            return 0
        # Find upper bound:
        for b in (2 ** i for i in itertools.count(1)):
            try:
                self._logicalint2physical(b)
            except IndexError:
                break
        a = 0
        while a < b:
            # INV: 0 = a < avg + 1 = length < b
            avg = a + (a + b) // 2
            try:
                self._logicalint2physical(avg)
                a = avg
            except IndexError:
                b = avg - 1
        return a + 1


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
        covered_count = self.selection.coverup(from_index, to_index)
        self._length -= covered_count

    def coverup_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index I_i, where @from_index <= i < @to_index, to become hidden. """
        covered_count = self.selection.coverup_virtual(from_index, to_index)
        self._length -= covered_count

    def uncover(self, from_index, to_index):
        """ Let N denote the total number of elements in the sequence. This method causes every element with index i,
        where @from_index <= i < @to_index, to become visible (if it is not already). """
        revealed_count = self.selection.reveal(from_index, to_index)
        self._length += revealed_count

    def uncover_virtual(self, from_index, to_index):
        """ Let I_0, I_1, ..., I_(M-1) denote the indices of the visible elements in the sequence. This method causes
        every element with index i, where I_@from_index < i < I_@to_index, to become visible. If @from_index is None,
        and @to_index is not None, the condition becomes i < I_@to_index. If @from_index is not None and @to_index is
        None, the condition becomes I_@from_index < i. If both are None, all elements in the sequence become visible.
        """
        revealed_count = self.selection.reveal(from_index, to_index)
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


class IROMMmap(SourcedGMmap, StringMmap):  # TODO rename
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


class SelectiveIROMMmap(SelectiveGMmap, IROMMmap):  # TODO rename

    def __init__(self, bytestring_iterator, codec):  # TODO reduce coupling, Hacker mediator
        super(SelectiveIROMMmap, self).__init__(bytestring_iterator, codec)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int):
        return slice(4 * location, 4 * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection):
        return location * 4
