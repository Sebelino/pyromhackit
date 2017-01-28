#!/usr/bin/env python

from prettytable import PrettyTable
import re
from ast import literal_eval
import difflib

from .reader import write
from .thousandcurses import codec
from .thousandcurses.codec import read_yaml

"""
Class representing a ROM.
"""


class Facet(object):
    """ A ROM paired with a string decoded from it and the relations between them.  """
    def __init__(self, bytestr, decoder):
        self.src = ROM(bytestr)
        self.decoder = decoder
        self.dst = decoder.decode(bytes(self.src))

    def source_diffusion(self, idx):
        """ Returns the indices of the bytes in the ROM affected
        when altering the ith character of the decoded string """
        self.src[idx]  # Raise IndexError?
        indices = set()
        for i in range(2**8):
            alteration = self.src[:idx]+bytes([i])+self.src[idx+1:]
            dalteration = self.decoder.decode(alteration)
            diff = difflib.ndiff(dalteration, self.dst)
            adiff = [ds for ds in diff if ds[0] != '+']
            for j, s in enumerate(adiff):
                if s[0] == '-':
                    indices.add(j)
        return indices

    def impose_character(self, byteidx, stridx, c):
        """ By modifying the byteidx'th byte, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """

    def impose_byte(self, stridx, byteidx, b):
        """ By modifying the stridx'th character, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """

    def __repr__(self):
        if len(self.src) <= 30:
            srcstr = "Facet({},".format(self.src)
        else:
            srcstr = "Facet({}{}{},".format(self.src[:20], "...", self.src[len(self.src)-7:])
        if len(self.dst) <= 30:
            dststr = "      {})".format(self.dst)
        else:
            dststr = "      {}{}{},".format(self.dst[:20], "...", self.dst[len(self.dst)-7:])
        return "{}\n{}".format(srcstr, dststr)


class ROM(object):
    """ A fancier kind of bytestring, designed to be easier to read and edit. """

    def __init__(self, *args, **kwargs):
        if 'path' in kwargs:
            path = kwargs['path']
            with open(path, 'rb') as f:
                self.content = f.read()
        else:
            self.content = bytes(*args)

    def index(self, bstring):
        return self.content.index(bstring)

    def index_regex(self, bregex):
        """ Returns a pair (a, b) which are the start and end indices of the first string found when searching the ROM
        using the specified regex, or None if there is none. """
        match = re.search(bregex, self.content)
        if match:
            return match.span()

    def relative_search(self, bregex, stop_on_match=True):
        """ Returns a dictionary mapping a byte offset to a pair (a, b) which are the indices of the strings found when
        doing an offset search. """
        results = dict()
        for i in range(2**8):
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
            tbl = [self.content[i*w:(i+1)*w]
                   for i in range(int(len(self)/w)+1)]
            if tbl[-1] == b'':
                return tbl[:-1]
            return tbl
        else:
            return [self.content]

    @staticmethod
    def labeltable(tbl):
        """ [[String]] (NxM) -> [[String]] (NxM+1) """
        width = len(tbl[0])
        return [[("%06x:" % (i*width)).upper()]+tbl[i]
                for i in range(len(tbl))]

    def offset(self, n):
        """ Increase the value of each byte in the ROM by n modulo 256 """
        return ROM([(b + n) % 2**8 for b in self])

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
            segment = stream[i:i+cols]
            segment = segment+" "*max(0, cols-len(segment))
            segment = list(segment)
            if label:
                fmtstr = "{:>"+str(labelwidth)+"}: "
                segment = [fmtstr.format(i)]+segment
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
            return lambda s: write(s.content, path) if \
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
        return len(self.content)

    def __eq__(self, other):
        return isinstance(other, ROM) and self.content == other.content

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.content.__lt__(other.content)

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.content[val]
        if isinstance(val, slice):
            return ROM(self.content[val.start:val.stop:val.step])

    def __hash__(self):
        return hash(repr(self))

    def str_contracted(self, max_width):
        # TODO left_weight parameter?
        """ Returns a string displaying the ROM with at most max_width characters. """
        if max_width < 8:
            raise ValueError("ROM cannot be displayed with less than 8 characters.")
        head = list("ROM(b''")
        tail = list("...b'')")
        max_width = 80
        if len(repr(self)) <= max_width:
            return repr(self)
        left_weight = 2
        it = iter(self.content)
        rit = reversed(self.content)
        byte_iter = zip(*[it] * left_weight, rit)
        byte_iter = iter(y for x in byte_iter for y in x)
        for i in range(len(self)):
            b = bytes([next(byte_iter)])
            br = repr(b)[2:-1]
            room_available = len(head) + len(tail) + len(br) <= max_width
            if not room_available:
                break
            if i % (left_weight + 1) == left_weight:
                tail[5:5] = list(br)
            elif room_available:
                head[-1:-1] = list(br)
        return "".join(head+tail)

    def __str__(self):
        return self.str_contracted(80)

    def __repr__(self):
        return "ROM({})".format(self.content)
