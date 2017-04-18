#!/usr/bin/env python

from prettytable import PrettyTable
import re
from ast import literal_eval

from .reader import write
from .thousandcurses import codec
from .thousandcurses.codec import read_yaml, Tree

"""
Class representing a ROM.
"""


def singleton_structure(bytestr):
    return [bytestr]


class ROM(object):
    """ A fancier kind of bytestring, bytestream, or handle to a file, designed to be easier to read and edit. """

    def __init__(self, rom_specifier, structure=singleton_structure):
        """ Constructs a ROM object from either a sequence of bytes or a path to a file to be read. You may define a
        hierarchical structure on the ROM by passing a function which takes a bytestring and returns a nested list
        of bytestrings. """
        if isinstance(rom_specifier, str):
            path = rom_specifier
            with open(path, 'rb') as f:
                bytestr = f.read()
        else:
            try:
                bytestr = bytes(rom_specifier)
            except:
                raise ValueError("ROM constructor expected a bytestring-compatible object or path, got: {}".format(
                    type(rom_specifier)))
        self.content = Tree(structure(bytestr))

    def index(self, bstring):
        return self.content[0].index(bstring)

    def index_regex(self, bregex):
        """ Returns a pair (a, b) which are the start and end indices of the first string found when searching the ROM
        using the specified regex, or None if there is none. """
        match = re.search(bregex, self.content[0])
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
            tbl = [self.content[0][i * w:(i + 1) * w]
                   for i in range(int(len(self) / w) + 1)]
            if tbl[-1] == b'':
                return tbl[:-1]
            return tbl
        else:
            return [self.content[0]]

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
            return lambda s: write(s.content[0], path) if \
                isinstance(s, ROM) else write(s, path)
        raise Exception("Could not execute: {}".format(execstr))

    def pipe(self, *pipeline):
        filters = []
        for subpipeline in pipeline:
            if not isinstance(subpipeline, str):
                filter = subpipeline
                filters.append(filter)
                continue
            pline = [f.strip() for f in subpipeline.split("|")]
            for execstr in pline:
                filter = ROM.execute(execstr)
                filters.append(filter)
        stream = self
        for f in filters:
            stream = f(stream)
        return stream

    def __len__(self):
        return len(self.content[0])

    def __eq__(self, other):
        return isinstance(other, ROM) and self.content[0] == other.content[0]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.content[0].__lt__(other.content[0])

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.content[0][val]
        if isinstance(val, slice):
            return ROM(self.content[0][val.start:val.stop:val.step])
        raise TypeError("ROM indices must be integers or slices, not {}".format(type(val).__name__))

    def __add__(self, operand):
        return ROM(self.content[0] + operand)

    def __radd__(self, operand):
        return ROM(operand + self.content[0])

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
        if max_width < len("ROM(...)") + len(repr(bytes([self.content[0][0]]))):
            return "ROM(...)"
        left_weight = 2  # Soft-code? Probably not worth the effort.
        # If non-empty head bytestring:
        result = list("ROM(b''...)")
        head = []
        tail = []
        it = iter(self.content[0])
        rit = reversed(self.content[0])
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

    def __str__(self):
        return "ROM({})".format(self.content[0])
