#!/usr/bin/env python

import argparse
import yaml
import sys
import string
from prettytable import PrettyTable
import re
from ast import literal_eval

from .reader import write
from .thousandcurses import codec
from .thousandcurses.codec import read_yaml

"""
Class representing a ROM.
"""


class ROM(object):
    def __init__(self, *args, **kwargs):
        if 'path' in kwargs:
            path = kwargs['path']
            with open(path, 'rb') as f:
                self.content = f.read()
        else:
            self.content = bytes(*args)

    def index(self, bstring):
        return self.content.index(bstring)

    def lines(self, width):
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

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.content[val]
        if isinstance(val, slice):
            return ROM(self.content[val.start:val.stop:val.step])

    def __str__(self):
        return self.pipe("hex | join ' '")

    def __repr__(self):
        if len(self) <= 30:
            return "ROM({})".format(self.content)
        return "ROM({}{}{})".format(self.content[:20],
                "...", self.content[len(self.content)-7:])
