#!/usr/bin/env python
from abc import abstractmethod, ABCMeta
from collections import namedtuple
import io

from prettytable import PrettyTable
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
    sequence of elements of any type(s) satisfying the following condition:
    * The bytestring representation of a sequence equals the concatenation of the individual elements' bytestring
      representations.
    """

    def __init__(self, *args):  # Final
        """ Creates an instance from @source. """
        source = self._args2source(*args)
        self._content = self._source2mmap(source)
        if isinstance(source, io.IOBase):
            self._length = self._compute_length()
        else:
            self._length = len(source)

    def _args2source(self, *args):
        """ :return The source (file or sequence) contained in the arguments @args. """
        return args

    def _source2mmap(self, source):  # Final
        """ :return a mmap from @source, which can be either a sequence or a file storing the sequence. """
        if isinstance(source, io.IOBase):
            m = self._file2mmap(source)
        else:
            m = self._sequence2mmap(source)
        assert isinstance(m, mmap.mmap)
        return m

    def _sequence2mmap(self, sequence) -> mmap.mmap:  # Final
        """ :return An anonymous mmap storing the bytestring representation of the sequence @sequence. @sequence needs
        to either be a bytestring or contain only elements that implement __len__. """
        if isinstance(sequence, bytes):
            m = mmap.mmap(-1, len(sequence))
            m.write(sequence)
            return m
        capacity = len(sequence)  # Initial capacity
        m = mmap.mmap(-1, capacity)
        currentsize = 0
        for element in sequence:
            bs = self._encode(element)
            currentsize += len(bs)
            while currentsize > capacity:
                capacity *= 2
                m.resize(capacity)  # Double capacity if overflow
            m.write(bs)
        m.resize(currentsize)
        return m

    def _file2mmap(self, file) -> mmap.mmap:  # Final
        """ :return A mmap storing the bytestring representation of the sequence originating from the file @file. """
        protection = self._access()
        m = mmap.mmap(file.fileno(), 0, access=protection)
        return m

    @abstractmethod
    def _compute_length(self) -> int:
        """ :return The length of the sequence originating from the file @file. """
        raise NotImplementedError()

    def _access(self):
        """ :return The memory protection of the memory-mapped file. By default, readable and writable. """
        return mmap.ACCESS_READ | mmap.ACCESS_WRITE

    @abstractmethod
    def _logical2physical(self, location) -> slice:
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence.
        :raise IndexError if @location is out of bounds. """
        raise NotImplementedError()

    @abstractmethod
    def _encode(self, element):
        """ :return The bytestring that @element encodes into. """
        raise NotImplementedError()

    @abstractmethod
    def _decode(self, bytestring):
        """ :return The element that @bytestring encodes. """
        raise NotImplementedError()

    def __getitem__(self, location):  # Final
        """ :return The @location'th element, if @location is an integer; or the sub-sequence retrieved when slicing the
        sequence with @location, if @location is a slice. """
        bytestringlocation = self._logical2physical(location)
        bytestringrepr = self._content[bytestringlocation]
        value = self._decode(bytestringrepr)
        return value

    def __setitem__(self, location, val):  # Final
        """ Sets the @location'th element to @val, if @location is an integer; or sets the sub-sequence retrieved when
        slicing the sequence with @location to @val, if @location is a slice. There should be no reason to override
        this. """
        bytestringrepr = self._encode(val)
        bytestringlocation = self._logical2physical(location)
        self._content[bytestringlocation] = bytestringrepr

    def __len__(self):
        """ :return The number of elements in the sequence. """
        return self._length


class IndexedGMmap(GMmap):
    """ GMmap where the indices used to access elements in the sequence are either integers or slices. """

    def _logical2physical(self, location) -> slice:
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence.
        :raise IndexError if @location is an integer and is out of bounds. """
        if isinstance(location, int):
            return self._logicalint2physical(location)
        elif isinstance(location, slice):
            return self._logicalslice2physical(location)
        else:
            raise ValueError("Unexpected location type: {}".format(type(location)))

    @abstractmethod
    def _logicalint2physical(self, location: int) -> slice:
        """ :return The slice for the bytestring that encodes the element(s) at integer index @location of the sequence.
        :raise IndexError if @location is out of bounds. """
        raise NotImplementedError()

    @abstractmethod
    def _logicalslice2physical(self, location: slice) -> slice:
        """ :return The slice for the bytestring that encodes the element(s) at location @location of the sequence. """
        raise NotImplementedError()


class BytesMmap(IndexedGMmap):
    """ A GMmap which is a sequence of elements where each element is a bytestring of any positive length. """

    def _decode(self, bytestring):
        return bytestring

    def _encode(self, element):
        return element


class FixedWidthBytesMmap(BytesMmap):
    """ A GMmap which is a sequence of bytestrings where all bytestrings share the same (positive) length. """

    def _args2source(self, width, source):
        self.width = width
        return source

    def _logicalint2physical(self, location: int):
        if 0 <= location < len(self):
            return slice(self.width * location, self.width * (location + 1))
        elif -len(self) <= location < -1:
            return slice(self.width * location, self.width * (location + 1))
        elif location == -1:
            return slice(self.width * location, None)
        if location < -len(self) or location >= len(self):
            raise IndexError("Index out of bounds: {}".format(location))

    def _logicalslice2physical(self, location: slice):
        return slice(
            self.width * location.start if location.start else None,
            self.width * location.stop if location.stop else None,
            self.width * location.step if location.step else None,
        )

    def _compute_length(self):
        return len(self._content) / self.width


class Memory(object):
    @abstractmethod
    def tree(self) -> Tree:
        raise NotImplementedError()

    @abstractmethod
    def __len__(self):
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError()

    def __ne__(self, other):
        return not self.__eq__(other)

    @abstractmethod
    def __lt__(self, other):
        raise NotImplementedError()

    @abstractmethod
    def __getitem__(self, val):
        raise NotImplementedError()

    @abstractmethod
    def __add__(self, operand):
        raise NotImplementedError()

    @abstractmethod
    def __radd__(self, operand):
        raise NotImplementedError()


class ROM(Memory):
    """ Read-only memory image. Basically a handle to a file, designed to be easy to read. As you might not be
    interested in reading the whole file, you may optionally select the portions of the file that should be revealed.
    By default, the whole file is revealed. """

    def __init__(self, rom_specifier, structure=SingletonTopology()):
        """ Constructs a ROM object from a path to a file to be read. You may define a hierarchical structure on the
        ROM by passing a Topology instance. """
        # TODO ...or a BNF grammar
        self.structure = structure
        if isinstance(rom_specifier, str):
            path = rom_specifier
            filesize = os.path.getsize(path)
            file = open(path, 'r')
            content = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ)
            self.source = {
                'path': path,
                'size': filesize,
                'file': file,
                'content': content,
                'atomcount': structure.length(filesize),
            }
            self.selection = Selection(slice(0, filesize))
        else:
            try:
                bytestr = bytes(rom_specifier)
                if not bytestr:  # mmaps cannot have zero length
                    raise NotImplementedError("The bytestring's length cannot be zero.")
                size = len(bytestr)
                content = mmap.mmap(-1, size)  # Anonymous memory
                content.write(bytestr)
                content.seek(0)
                self.source = {
                    'size': size,
                    'content': content,
                    'atomcount': structure.length(size),
                }
                self.selection = Selection(slice(0, len(bytestr)))
            except:
                raise ValueError("ROM constructor expected a bytestring-convertible object or path, got: {}".format(
                    type(rom_specifier)))

    def coverup(self, from_index, to_index, virtual=False):  # Mutability
        self.selection.coverup(from_index, to_index)

    def reveal(self, from_index, to_index, virtual=False):  # Mutability
        self.selection.reveal(from_index, to_index)

    def tree(self):
        """ Returns a Tree consisting of the revealed portions of the ROM according to the ROM's topology. """
        bs = self.selection.select(self.source['content'])
        t = self.structure.structure(bs)
        return Tree(t)

    def traverse_preorder(self):  # NOTE: 18 times slower than iterating for content with getatom
        for idx, atomidx, idxpath, content in self.structure.traverse_preorder(self):
            Atom = namedtuple("Atom", "index atomindex indexpath physindex content")
            physidx = self.selection.virtual2physical(idx)
            yield Atom(idx, atomidx, idxpath, physidx, bytes(content))

    def flatten_without_joining(self):
        return self.content.flatten_without_joining()

    def index(self, bstring):
        return bytes(self.source['content']).index(bstring)

    def index_regex(self, bregex):
        """ Returns a pair (a, b) which are the start and end indices of the first string found when searching the ROM
        using the specified regex, or None if there is none. """
        match = re.search(bregex, bytes(self.source['content']))
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
            tbl = [bytes(self.source['content'])[i * w:(i + 1) * w]
                   for i in range(int(len(self) / w) + 1)]
            if tbl[-1] == b'':
                return tbl[:-1]
            return tbl
        else:
            return [bytes(self.source['content'])]

    @staticmethod
    def labeltable(tbl):
        # TODO This should really be moved to codecs
        """ [[String]] (NxM) -> [[String]] (NxM+1) """
        width = len(tbl[0])
        return [[("%06x:" % (i * width)).upper()] + tbl[i]
                for i in range(len(tbl))]

    def offset(self, n):
        """ Increase the value of each byte in the ROM by n modulo 256 """
        return ROM([(b + n) % 2 ** 8 for b in self])

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
            return lambda s: write(bytes(s.source['content']), path) if \
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
        """ Returns a generator for every byte in the ROM. """
        for b in self.source['content']:
            yield b

    def __len__(self):
        """ Returns the number of bytes in this ROM. """
        return self.source['size']

    def atomcount(self):
        return self.source['atomcount']

    def __eq__(self, other):
        """ True of both are ROMs and their byte sequences are the same. """
        # TODO Should the paths also be equal? What about the selections?
        return isinstance(other, ROM) and bytes(self) == bytes(other)

    def __hash__(self):
        return hash(bytes(self))

    def __lt__(self, other: 'ROM'):
        return bytes(self.source['content']).__lt__(bytes(other.source['content']))

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.source['content'][self.selection.virtual2physical(val)]
        if isinstance(val, slice):
            subselection = self.selection.virtual2physicalselection(val)
            bs = subselection.select(self.source['content'])
            return ROM(bs, structure=self.structure)
        raise TypeError("ROM indices must be integers or slices, not {}".format(type(val).__name__))

    def getatom(self, atomindex):
        """ :return The @atomindex'th atom in this memory. """
        return bytes(self.structure.getleaf(atomindex, self))

    def indexpath2entry(self, indexpath):
        Atom = namedtuple("Atom", "index atomindex indexpath physindex content")
        index = self.structure.indexpath2index(indexpath)
        atomindex = self.structure.index2leafindex(index)
        physindex = self.selection.virtual2physical(index)
        content = self.getatom(atomindex)
        return Atom(index, atomindex, indexpath, physindex, content)

    def __add__(self, operand):
        return ROM(bytes(self.source['content']) + operand)

    def __radd__(self, operand):
        return ROM(operand + self.source['content'])

    def str_contracted(self, max_width):
        """ Returns a string displaying the ROM with at most max_width characters. """
        # If too cramped:
        if max_width < 8:
            raise ValueError("ROM cannot be displayed with less than 8 characters.")
        # If entire string fits:
        if len(str(self)) <= max_width:
            return str(self)
        # If no bytestring fits:
        if max_width < len("ROM(...)") + len(repr(bytes([self[0]]))):
            return "ROM(...)"
        left_weight = 2  # Soft-code? Probably not worth the effort.
        # If non-empty head bytestring:
        result = list("ROM(b''...)")
        head = []
        tail = []
        it = iter(bytes(self.source['content']))
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
        m = self.source['content']
        s = self.selection.select(m)
        bs = s[:]
        self.source['content'].seek(0)
        return bs

    def __str__(self):
        """ Presents the content or path of the ROM. """
        topologystr = ""
        if not isinstance(self.structure, SingletonTopology):
            topologystr = ", structure={}".format(self.structure)
        if 'path' in self.source:
            return "ROM(path={}{})".format(repr(self.source['path']), topologystr)
        else:
            return "ROM({}{})".format(bytes(self), topologystr)


class IROM(Memory):
    """ Isomorphism of a ROM. Basically a Unicode string with a structure defined on it. """
    def __init__(self, rom: 'ROM', codec):
        """ Constructs an IROM object from a ROM and a codec transliterating every ROM atom into an IROM atom. """
        self.structure = SimpleTopology(1)  # This will do for now
        self.text_encoding = 'utf-32'
        self.source = {
            'size': rom.atomcount(),  # FIXME
        }
        content = self._write_to_mmap(rom, codec)
        self.source['content'] = content
        self.source['bytesize'] = len(content)
        self.source['atomcount'] = self.source['size']  # FIXME

    def _write_to_mmap(self, rom, codec):
        size = self.index2slice(rom.atomcount()-1).stop
        content = mmap.mmap(-1, size)  # Anonymous memory
        content.write(''.encode(self.text_encoding))
        #for _, _, _, _, atom in rom.traverse_preorder():
        for i in range(rom.source['atomcount']):
            atom = rom.getatom(i)
            s = codec[atom]
            content.write(s.encode('utf-32')[self.index2slice(0).start:])
        content.seek(0)
        return content

    def tree(self):
        t = self.structure.structure(self[:])
        return Tree(t)

    def traverse_preorder(self):
        for idx, atomidx, idxpath, content in self.structure.traverse_preorder(self):
            byteindex = self.index2slice(idx).start
            yield idx, atomidx, idxpath, byteindex, str(content)

    def index2slice(self, idx):
        """ Returns a slice indicating where the bytes necessary to encode the @idx'th character are stored. """
        if idx >= len(self):
            raise IndexError("IROM index out of range: {}".format(idx))
        modidx = idx % len(self)
        if self.text_encoding == 'utf-32':
            return slice(4 + 4 * modidx, 4 + 4 * (modidx + 1))
        raise NotImplementedError()

    def __getitem__(self, val):
        prefix = self.source['content'][0:self.index2slice(0).start]
        if isinstance(val, int):
            s = self.index2slice(val)
            return (prefix + self.source['content'][s]).decode(self.text_encoding)
        if isinstance(val, slice):
            a = self.index2slice(val.start).start if val.start else self.index2slice(0).start
            b = self.index2slice(val.stop-1).stop if val.stop else None
            return (prefix + self.source['content'][a:b]).decode(self.text_encoding)
        raise TypeError("ROM indices must be integers or slices, not {}".format(type(val).__name__))

    def getatom(self, atomindex):
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
        """ Returns the number of characters in this IROM. """
        return self.source['size']

    def atomcount(self):
        return self.source['atomcount']

    def __str__(self):
        if self.source['bytesize'] > 10**8:
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
        if isinstance(key, int) and isinstance(value, str):
            prefix = self.source['content'][0:self.index2slice(0).start]
            newatombytes = value.encode(self.text_encoding)[4:]
