#!/usr/bin/env python
from abc import abstractmethod, ABCMeta
from collections import namedtuple
import io

import math

import itertools
from typing import Optional, Union

import re
from ast import literal_eval
import os
import mmap
from math import ceil
from prettytable import PrettyTable

from pyromhackit.reader import write
from pyromhackit.thousandcurses import codec
from pyromhackit.thousandcurses.codec import read_yaml, Tree
from pyromhackit.selection import Selection
from pyromhackit.tree import SingletonTopology, SimpleTopology

"""
Class representing a ROM.
"""


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
    def _source2mmap(cls, source):
        if isinstance(source, io.TextIOWrapper):  # Source is file
            return cls._file2mmap(source)
        else:
            return cls._sequence2mmap(source)

    @classmethod
    def _sequence2mmap(cls, sequence) -> mmap.mmap:  # Final
        """ :return An anonymous mmap storing the bytestring representation of the sequence @sequence. @sequence needs
        to either be a bytestring or an iterable containing only elements that implement __len__. """

        def double_mmap_capacity(m):
            new_m = mmap.mmap(-1, capacity)
            new_m.write(bytes(m))  # FIXME Potentially large bytestring
            m.close()
            return new_m

        protection = cls._access()
        if isinstance(sequence, bytes):
            m = mmap.mmap(-1, len(sequence), access=protection)
            m.write(sequence)
            return m
        capacity = mmap.PAGESIZE  # Initial capacity. Cannot do len(sequence) since it is a generator.
        m = mmap.mmap(-1, capacity)
        currentsize = 0
        for element in sequence:
            bs = cls._encode(element)
            currentsize += len(bs)
            while currentsize > capacity:
                capacity *= 2
                m = double_mmap_capacity(m)  # Because m.resize() is apparently bugged and causes SIGBUS
            m.write(bs)
        m.resize(currentsize)
        return m

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


#class FixedWidthGMmap(GMmap, metaclass=ABCMeta):


class FixedWidthBytesMmap(SourcedGMmap, BytesMmap):
    """ A GMmap which is a sequence of bytestrings where all bytestrings share the same (positive) length. """

    def __init__(self, width, source):
        self.width = width
        self._content = self._source2mmap(source)
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


class ROM(object):
    """ Read-only memory image. Basically a handle to a file, designed to be easy to read. As you might not be
    interested in reading the whole file, you may optionally select the portions of the file that should be revealed.
    By default, the whole file is revealed. """

    def __init__(self, rom_specifier, structure=SimpleTopology(1)):
        """ Constructs a ROM object from a path to a file to be read. You may define a hierarchical structure on the
        ROM by passing a Topology instance. """
        # TODO ...or a BNF grammar
        self.structure = structure
        if isinstance(rom_specifier, str):
            path = rom_specifier
            filesize = os.path.getsize(path)
            file = open(path, 'r')
            self.memory = SelectiveFixedWidthBytesMmap(2, file)
        else:
            try:
                bytestr = bytes(rom_specifier)
            except TypeError:
                raise TypeError("ROM constructor expected a bytestring-convertible object or path, got: {}".format(
                    type(rom_specifier)))
            if not bytestr:  # mmaps cannot have zero length
                raise NotImplementedError("The bytestring's length cannot be zero.")
            size = len(bytestr)
            if str(structure) == "SimpleTopology(2)":
                self.memory = SelectiveFixedWidthBytesMmap(2, self.structure.structure(bytestr))
            else:
                # self.memory = SingletonBytesMmap(bytestr)
                self.memory = SelectiveFixedWidthBytesMmap(1, self.structure.structure(bytestr))

    def coverup(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.coverup_virtual(from_index, to_index)
        else:
            self.memory.coverup(from_index, to_index)

    def reveal(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.uncover_virtual(from_index, to_index)
        else:
            self.memory.uncover(from_index, to_index)

    def tree(self):
        """ Returns a Tree consisting of the revealed portions of the ROM according to the ROM's topology. """
        t = self.structure.structure(self.memory)
        return Tree(t)

    def traverse_preorder(self):  # NOTE: 18 times slower than iterating for content with getatom
        for idx, atomidx, idxpath, content in self.structure.traverse_preorder(self):
            Atom = namedtuple("Atom", "index atomindex indexpath physindex content")
            yield Atom(idx, atomidx, idxpath, idx, bytes(content))

    def flatten_without_joining(self):
        return self.content.flatten_without_joining()

    def index(self, bstring):
        return bytes(self).index(bstring)

    def index_regex(self, bregex):
        """ Returns a pair (a, b) which are the start and end indices of the first string found when searching the ROM
        using the specified regex, or None if there is none. """
        match = re.search(bregex, bytes(self))
        if match:
            return match.span()

    def relative_search(self, bregex, stop_on_match=True):
        """ Returns a dictionary mapping a byte offset to a pair (a, b) which are the indices of the strings found when
        doing an offset search. """
        results = dict()
        for i in range(2 ** 8):
            offset_rom = self.offset(i)
            match = offset_rom.index_regex(bregex)
            if match:
                results[i] = match
                if stop_on_match:
                    return results
        return results

    def lines(self, width):
        # TODO Return a list of ROMs instead?
        """ List of bytestring lines with the specified width """
        if width:
            w = width
            tbl = [bytes(self)[i * w:(i + 1) * w]
                   for i in range(int(len(self) / w) + 1)]
            if tbl[-1] == b'':
                return tbl[:-1]
            return tbl
        else:
            return [bytes(self)]

    @staticmethod
    def labeltable(tbl):
        # TODO This should really be moved to codecs
        """ [[String]] (NxM) -> [[String]] (NxM+1) """
        width = len(tbl[0])
        return [[("%06x:" % (i * width)).upper()] + tbl[i]
                for i in range(len(tbl))]

    def offset(self, n):
        """ :return A ROM where the value of each byte in the ROM is increased by @n modulo 256. """
        return ROM(bytes((b + n) % 2 ** 8 for b in self.iterbytes()), structure=self.structure)

    def map(self, mapdata):
        if isinstance(mapdata, dict):
            dct = mapdata
        if isinstance(mapdata, str):
            path = mapdata
            dct = read_yaml(path)
        return "".join(dct[byte] if byte in dct else chr(byte)
                       for byte in self)

    def table(self, width=0, labeling=False, encoding=codec.HexifySpaces.decode):
        """ (Labeled?) table where each cell corresponds to a byte """
        # encoded = self.encoding
        lines = self.lines(width)
        tbl = [[encoding(b) for b in row] for row in lines]
        ltbl = ROM.labeltable(tbl) if labeling else tbl
        return "\n".join(" ".join(lst) for lst in ltbl)

    @staticmethod
    def tabulate(stream, cols, label=False, border=False, padding=0):
        """ Display the stream of characters in a table. """
        table = PrettyTable(header=False, border=border, padding_width=padding)
        labelwidth = len(str(len(stream)))
        for i in range(0, len(stream), cols):
            segment = stream[i:i + cols]
            segment = segment + " " * max(0, cols - len(segment))
            segment = list(segment)
            if label:
                fmtstr = "{:>" + str(labelwidth) + "}: "
                segment = [fmtstr.format(i)] + segment
            table.add_row(segment)
        tablestr = str(table)
        return tablestr

    @staticmethod
    def execute(execstr):
        """ :return: A function that operates on a stream of bytes. """
        positionals = execstr.split()
        if positionals[0] == "latin1":
            return lambda s: s.decode("latin1")
        elif positionals[0] == "hex":
            return lambda s: codec.HexifySpaces.decode(s).split()
        elif positionals[0] == "odd":
            return lambda s: s[::2]
        elif positionals[0] == "join":
            if len(positionals) == 1:
                sep = ""
            else:
                whiteindex = re.search(r'\s', execstr).start()
                sep = execstr[whiteindex:].strip()
                try:
                    sep = literal_eval(sep)
                except ValueError:
                    pass
            return lambda s: sep.join(s)
        elif positionals[0] == "map":
            path = positionals[1]
            hexmap = read_yaml(path)
            return lambda s: "".join(hexmap[b] if b in hexmap.keys()
                                     else chr(b) for b in s)
        elif positionals[0] == "tabulate":
            cols = int(positionals[1])
            label = {"--label", "-l"}.intersection(positionals[2:]) != set()
            border = {"--border", "-b"}.intersection(positionals[2:]) != set()
            padding = {"--padding",
                       "-p"}.intersection(positionals[2:]) != set()
            return lambda s: ROM.tabulate(s, cols, label, border, padding)
        elif positionals[0] == "save":
            path = positionals[1]
            return lambda s: write(bytes(s), path) if \
                isinstance(s, ROM) else write(s, path)
        raise Exception("Could not execute: {}".format(execstr))

    def pipe(self, *pipeline):
        filters = []
        for subpipeline in pipeline:
            if not isinstance(subpipeline, str):
                pipe_filter = subpipeline
                filters.append(pipe_filter)
                continue
            pline = [f.strip() for f in subpipeline.split("|")]
            for execstr in pline:
                pipe_filter = ROM.execute(execstr)
                filters.append(pipe_filter)
        stream = self
        for f in filters:
            stream = f(stream)
        return stream

    def iterbytes(self):  # TODO only revealed
        """ :return A generator for every byte in the ROM. """
        return self.memory.iterbytes()

    def __len__(self):
        """ :return The number of bytes in this ROM. """
        return self.atomcount()

    def atomcount(self):
        """ :return The number of atoms in this ROM. """
        return len(self.memory)

    def bytecount(self):
        """ :return The number of bytes in this ROM. """
        return self.memory.bytecount()

    def __eq__(self, other):
        """ True of both are ROMs and their byte sequences are the same. """
        # TODO Should the paths also be equal? What about the selections?
        # TODO optimize with iter+zip.
        return isinstance(other, ROM) and bytes(self) == bytes(other)

    def __hash__(self):
        return hash(bytes(self))

    def __lt__(self, other: 'ROM'):
        return bytes(self).__lt__(bytes(other))

    def __getitem__(self, val):
        return self.getatom(val)

    def getatom(self, atomlocation):
        """ :return The @atomindex'th atom in this memory. """
        return self.memory[atomlocation]

    def indexpath2entry(self, indexpath):
        Atom = namedtuple("Atom", "index atomindex indexpath physindex content")
        index = self.structure.indexpath2index(indexpath)
        atomindex = self.structure.index2leafindex(index)
        physindex = -1  # TODO
        content = self.getatom(atomindex)
        return Atom(index, atomindex, indexpath, physindex, content)

    def __add__(self, operand):
        return ROM(self.memory + operand)

    def __radd__(self, operand):
        return ROM(operand + self.memory)

    def str_contracted(self, max_width):
        """ Returns a string displaying the ROM with at most max_width characters. """
        # If too cramped:
        if max_width < 8:
            raise ValueError("ROM cannot be displayed with less than 8 characters.")
        # If entire string fits:
        if len(str(self)) <= max_width:
            return str(self)
        # If no bytestring fits:
        if max_width < len("ROM(...)") + len(repr(self[0])):
            return "ROM(...)"
        left_weight = 2  # Soft-code? Probably not worth the effort.
        # If non-empty head bytestring:
        result = list("ROM(b''...)")
        head = []
        tail = []
        it = iter(bytes(self))
        rit = reversed(bytes(self))
        byte_iter = zip(*[it] * left_weight, rit)
        byte_iter = iter(y for x in byte_iter for y in x)
        tail_surroundings_len = 0
        for i in range(len(self)):
            b = bytes([next(byte_iter)])
            is_tail_byte = i % (left_weight + 1) == left_weight
            br = repr(b)[2:-1]
            if is_tail_byte and not tail:
                tail_surroundings_len = len("b''")
            room_available = len("".join(result + head + tail)) + len(br) + tail_surroundings_len <= max_width
            if not room_available:
                break
            if is_tail_byte:
                tail.insert(0, br)
            else:
                head.append(br)
        if tail:
            tail.insert(0, "b'")
            tail.append("'")
        result[6:6] = head
        result[-1:-1] = tail
        return "".join(result)

    def __bytes__(self):
        bs = self.memory[:]
        return bs

    def __str__(self):
        """ Presents the content or path of the ROM. """
        topologystr = ""
        if not str(self.structure) == "SimpleTopology(1)":
            topologystr = ", structure={}".format(self.structure)
        if self.memory.path:
            return "ROM(path={}{})".format(repr(self.memory.path), topologystr)
        else:
            return "ROM({}{})".format(bytes(self), topologystr)


class IROMMmap(SourcedGMmap, StringMmap):
    """ A StringMmap where the source is extracted from a ROM and a codec mapping ROM atoms to strings. """

    def __init__(self, rom: ROM, codec):
        source = (codec[atom] for atom in rom)
        self._content = self._source2mmap(source)
        self._length = rom.atomcount()
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


class SelectiveIROMMmap(SelectiveGMmap, IROMMmap):

    def __init__(self, rom: ROM, codec):
        super(SelectiveIROMMmap, self).__init__(rom, codec)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int):
        return slice(4 * location, 4 * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection):
        return location * 4


class IROM(object):
    """ Isomorphism of a ROM. Basically a Unicode string with a structure defined on it. """

    def __init__(self, rom: 'ROM', codec):
        """ Constructs an IROM object from a ROM and a codec transliterating every ROM atom into an IROM atom. """
        self.structure = SimpleTopology(1)  # This will do for now
        self.text_encoding = 'utf-32'
        self.memory = SelectiveIROMMmap(rom, codec)

    def coverup(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.coverup_virtual(from_index, to_index)
        else:
            self.memory.coverup(from_index, to_index)

    def reveal(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.uncover_virtual(from_index, to_index)
        else:
            self.memory.uncover(from_index, to_index)

    def tree(self):
        t = self.structure.structure(self[:])
        return Tree(t)

    def traverse_preorder(self):
        for idx, atomidx, idxpath, content in self.structure.traverse_preorder(self):
            byteindex = self.index2slice(idx).start
            yield idx, atomidx, idxpath, byteindex, str(content)

    def index2slice(self, idx):  # TODO Abstraction leak -- remove (?)
        """ Returns a slice indicating where the bytes necessary to encode the @idx'th character are stored. """
        if idx >= len(self):
            raise IndexError("IROM index out of range: {}".format(idx))
        modidx = idx % len(self)
        if self.text_encoding == 'utf-32':
            return slice(4 + 4 * modidx, 4 + 4 * (modidx + 1))
        raise NotImplementedError()

    def __getitem__(self, val):
        return self.memory[val]

    def getatom(self, atomindex):  # TODO duplicate of getitem at this point
        """ :return The @atomindex'th atom in this memory. """
        return str(self.structure.getleaf(atomindex, self))

    def atomindex2entry(self, atomindex: int):
        Atom = namedtuple("Atom", "index atomindex indexpath byteindex content")
        indexpath = self.structure.leafindex2indexpath(atomindex)
        index = self.structure.indexpath2index(indexpath)
        content = self.getatom(atomindex)
        byteindex = self.index2slice(index).start
        return Atom(index, atomindex, indexpath, byteindex, content)

    def __len__(self):
        """ :return The number of characters in this IROM. """
        return len(self.memory)

    def atomcount(self):  # TODO __len__ duplicate (?)
        return len(self.memory)

    def __str__(self):
        if len(self.memory) > 10 ** 7:  # Assumes that IROM atoms are on average short
            raise MemoryError("IROM too large to convert to string")
        return self[:]

    def find(self, *args):
        return str(self).find(*args)

    def finditer(self, pattern):
        """ Returns an ordered list of matches with span=(a, b) such that self[a:b] matches @pattern. """
        return re.finditer(pattern, str(self))

    def first_match(self, pattern):
        """ Return the first match for the given pattern. """
        return next(self.finditer(pattern))

    def first_group(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).group(1)

    def first_group_index(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).start(1)

    def grep(self, pattern, context=50, labels=True):
        for m in self.finditer(pattern):
            s = m.string[m.start() - context:m.end() + context]
            label = ""
            if labels:
                label = "{}: ".format(hex(m.start()))
            print("{}{}".format(label, s))

    def table(self, cols=16, label=True, border=True, padding=1):
        """ Display the stream of characters in a table. """
        fields = [''] + [hex(i)[2:] for i in range(cols)]
        table = PrettyTable(field_names=fields, header=True, border=border, padding_width=padding)
        content = str(self)
        labelwidth = len(str(len(content)))
        for i in range(0, len(content), cols):
            segment = content[i:i + cols]
            segment = segment + " " * max(0, cols - len(segment))
            segment = list(segment)
            if label:
                fmtstr = "{:>" + str(labelwidth) + "}: "
                segment = [fmtstr.format(hex(i)[2:])] + segment
            table.add_row(segment)
        return table

    def grep_table(self, searchstring, context=3, cols=16, label=True, border=True, padding=1):
        s = str(self)
        idx = s.index(searchstring)
        tbl = self.table(cols, label, border, padding)
        arow = int(idx / cols) - context
        brow = int(idx / cols) + ceil(len(searchstring) / cols) + context
        return tbl[arow:brow]

    def __setitem__(self, key, value):
        raise NotImplementedError()  # TODO

    def dump(self, path):
        """ Writes the content of this IROM to a file with path @path. """
        with open(path, 'w') as f:
            f.write(self.memory[:])
