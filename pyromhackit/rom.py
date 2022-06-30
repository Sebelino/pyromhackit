#!/usr/bin/env python
from collections import namedtuple
from copy import deepcopy

import re
from ast import literal_eval
import os
from prettytable import PrettyTable

from pyromhackit.gmmap import SelectiveFixedWidthBytesMmap
from pyromhackit.reader import write
from pyromhackit.thousandcurses import codec
from pyromhackit.thousandcurses.codec import read_yaml, Tree
from pyromhackit.tree import SimpleTopology

"""
Class representing a ROM.
"""

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

    def selection(self):
        return deepcopy(self.memory.selection)

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
    def tabulate(stream, cols, label=False, border=False, padding=False):
        """ Display the stream of characters in a table. """
        table = PrettyTable(header=False, border=border, padding_width=int(padding))
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
