#!/usr/bin/env python

from prettytable import PrettyTable
import re
from ast import literal_eval
import os
import mmap

from pyromhackit.reader import write
from pyromhackit.thousandcurses import codec
from pyromhackit.thousandcurses.codec import read_yaml, Tree
from selection import Selection
from tree import SingletonTopology

"""
Class representing a ROM.
"""


def singleton_structure(bytestr):
    return [bytestr]


class ROM(object):
    """ Read-only memory image. Basically a handle to a file, designed to be easy to read. As you might not be
    interested in reading the whole file, you may optionally select the portions of the file that should be revealed.
    By default, the whole file is revealed. """

    def __init__(self, rom_specifier, structure=SingletonTopology):
        """ Constructs a ROM object from a path to a file to be read. You may define a hierarchical structure on the
        ROM by passing a function which takes a bytestring and returns a nested list of bytestrings. """
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
            }
            self.selection = Selection(slice(0, filesize))
        else:
            try:
                bytestr = bytes(rom_specifier)
                content = mmap.mmap(-1, len(bytestr))  # Anonymous memory
                content.write(bytestr)
                content.seek(0)
                size = len(bytestr)
                self.source = {
                    'size': size,
                    'content': content,
                }
                self.selection = Selection(slice(0, len(bytestr)))
            except:
                raise ValueError("ROM constructor expected a bytestring-compatible object or path, got: {}".format(
                    type(rom_specifier)))

    def coverup(self, from_index, to_index, virtual=False):  # Mutability
        self.selection.coverup(from_index, to_index)

    def reveal(self, from_index, to_index, virtual=False):  # Mutability
        self.selection.reveal(from_index, to_index)

    def show(self):
        return self.selection[self.content]

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

    def __len__(self):
        return self.source['size']

    def __eq__(self, other):
        # TODO Should the paths also be equal? What about the selections?
        return isinstance(other, ROM) and bytes(self) == bytes(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other: 'ROM'):
        return bytes(self.source['content']).__lt__(bytes(other.source['content']))

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.source['content'][val]
        if isinstance(val, slice):
            return ROM(self.source['content'][val.start:val.stop:val.step])
        raise TypeError("ROM indices must be integers or slices, not {}".format(type(val).__name__))

    def __add__(self, operand):
        return ROM(bytes(self.source['content']) + operand)

    def __radd__(self, operand):
        return ROM(operand + self.source['content'])

    def __hash__(self):
        return hash(str(self))

    def str_contracted(self, max_width):
        """ Returns a string displaying the ROM with at most max_width characters. """
        # If too cramped:
        if max_width < 8:
            raise ValueError("ROM cannot be displayed with less than 8 characters.")
        # If entire string fits:
        if len(str(self)) <= max_width:
            return str(self)
        # If no bytestring fits:
        if max_width < len("ROM(...)") + len(repr(bytes([self.source['content'][0]]))):
            return "ROM(...)"
        left_weight = 2  # Soft-code? Probably not worth the effort.
        # If non-empty head bytestring:
        result = list("ROM(b''...)")
        head = []
        tail = []
        it = iter(bytes(self.source['content']))
        rit = reversed(bytes(self.source['content']))
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
        bs = self.source['content'].read()
        self.source['content'].seek(0)
        return bs

    def __str__(self):
        if 'path' in self.source:
            return "ROM({})".format(repr(self.source['path']))
        else:
            return "ROM({})".format(bytes(self.source['content']))
