#!/usr/bin/env python

import argparse
import yaml
import sys
import string
from prettytable import PrettyTable
from pdb import set_trace
from enum import Enum
import re
from ast import literal_eval

def filecontents(path):
    """ List of lines in a file specified by path. """
    with open(path, 'r', encoding='utf8') as f:
        content = f.readlines()
        return content

def read_yaml(path):
    """ YAML -> Dictionary. """
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct

def readbin(path):
    """ Read the specified file into a byte array (integers). """
    f = open(path, 'rb')
    bytes = list(f.read())
    return bytes


def compact(stream, cols):
    """ Output every character with nothing in-between, making a line break every cols characters.
        If cols = 0, output everything on one line. """
    output = []
    for i in range(len(stream)):
        if cols > 0 and i % cols == 0:
            output.append('\n')
        output.append(stream[i])
    return "".join(output).strip()

def pack(stream):
    """ Removes all whitespace. """
    whitespace = string.whitespace.replace("\n", "").replace("\r", "")
    output = [e for e in stream if e not in whitespace]
    return output

def convert(infile, inencoding, pipeline, width, transliterationfiles):
    """ Uses the inencoding to read the infile, does some transliteration and applies a sequence of additional processing filters. """
    contents = readbin(infile)
    contenttype = [int]
    mapfiles = iter(transliterationfiles) if transliterationfiles else iter([])
    def transliterate(stream):
        try:
            mapfile = next(mapfiles)
        except StopIteration:
            n = len([p for p in pipeline if p == "map"])
            raise Exception("Supplied too few MAPs (%s)." % n)
        map = read_yaml(mapfile)
        return [ord(map[b]) if b in map else b for b in stream]
    def replace(s):
        try:
            mapfile = next(mapfiles)
        except StopIteration:
            n = len([p for p in pipeline if p == "replace"])
            raise Exception("Supplied too few REPLACEs (%s)." % n)
        map = read_yaml(mapfile)
        newstr = s
        for k in map:
            newstr = newstr.replace(k, map[k])
        return newstr
    def label(stream):
        return [("%06x: " % i).upper()+stream[i] if i % width == 0 else stream[i] for i in range(len(stream))]
    pipe = {
        "hex": ([int], [str], lambda lst: [("0"+hex(n)[2:])[-2:].upper() for n in lst]),
        "text": ([int], [str], lambda lst: [chr(n) for n in lst]),
        "odd": (None, None, lambda lst: lst[::2]),
        "pack": ([str], str, pack),
        "map": (None, None, lambda lst: transliterate(lst)),
        "replace": (str, str, lambda s: replace(s)),
        "join": ([str], str, lambda lst: "".join(lst)),
        "table": (None, str, lambda lst: tabulate(lst, width)),
        "label": ([str], [str], lambda lst: label(lst)),
    }
    labelingoffset = 0
    for filter in pipeline:
        if filter == "label":
            labelingoffset = 8
        (inputtype, outputtype, operation) = pipe[filter]
        if inputtype not in [None, contenttype]:
            raise Exception("Filter %s expected type %s, got %s" % (filter, inputtype, contenttype))
        contents = operation(contents)
        if outputtype is not None: contenttype = outputtype
    contents = compact(contents, width+labelingoffset)
    return contents

def write(content, path):
    """ Helper method for writing a bytestring or UTF-8 string to file """
    if isinstance(content, str):
        with open(path, "w", encoding="utf8") as f:
            print(content, end="", file=f)
            return
    elif isinstance(content, bytes):
        with open(path, "wb") as f:
            f.write(content)
            return
    raise Exception("Illegal type: {}".format(type(content)))

class ROM:
    def __init__(self, *args, **kwargs):
        if 'path' in kwargs:
            path = kwargs['path']
            with open(path, 'rb') as f:
                self.content = f.read()
        else:
            self.content = bytes(*args)

    def lines(self, width):
        """ List of bytestring lines with the specified width """
        if width:
            w = width
            tbl = [self.content[i*w:(i+1)*w] for i in range(int(len(self)/w)+1)]
            if tbl[-1] == b'':
                return tbl[:-1]
            return tbl
        else:
            return [self.content]

    @staticmethod
    def labeltable(tbl):
        """ [[String]] (NxM) -> [[String]] (NxM+1) """
        width = len(tbl[0])
        return [[("%06x:" % (i*width)).upper()]+tbl[i] for i in range(len(tbl))]

    @staticmethod
    def hex(bytestr):
        """ Bytestring -> [String] """
        return [("0"+hex(b)[2:])[-2:].upper() for b in bytestr]

    def map(self, mapdata):
        if isinstance(mapdata, dict):
            dct = mapdata
        if isinstance(mapdata, str):
            path = mapdata
            dct = read_yaml(path)
        return "".join(dct[byte] if byte in dct else chr(byte) for byte in self)

    def table(self, width=0, labeling=False, encoding=hex):
        """ (Labeled?) table where each cell corresponds to a byte """
        #encoded = self.encoding
        lines = self.lines(width)
        tbl = [[encoding(b) for b in row] for row in lines]
        ltbl = labeltable(tbl) if labeling else tbl
        return "\n".join(" ".join(lst) for lst in ltbl)

    @staticmethod
    def tabulate(stream, cols, label=False, border=False):
        """ Display the stream of characters in a table. """
        table = PrettyTable(header=False, border=border, padding_width=0)
        for i in range(0, len(stream), cols):
            segment = stream[i:i+cols]
            row = segment+" "*max(0, cols-len(segment))
            table.add_row(row)
        return str(table)

    @staticmethod
    def execute(execstr):
        """ :return: A function that operates on a stream of bytes. """
        positionals = execstr.split()
        if positionals[0] == "latin1":
            return lambda s: s.decode("latin1")
        elif positionals[0] == "hex":
            return lambda s: ROM.hex(s)
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
            map = read_yaml(path)
            return lambda s: "".join(map[b] for b in s)
        elif positionals[0] == "tabulate":
            cols = int(positionals[1])
            label = {"--label", "-l"}.intersection(positionals[2:]) != set()
            border = {"--border", "-b"}.intersection(positionals[2:]) != set()
            return lambda s: ROM.tabulate(s, cols, label, border)
        elif positionals[0] == "save":
            path = positionals[1]
            return lambda s: write(s.content, path) if isinstance(s, ROM) else write(s, path)
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
        return "ROM({})".format(self.content)

"""
Make a copy:
$ ./reader.py mt2.sfc out copy.sfc
Transliterate bytes into kana or latin characters:
$ ./reader.py mt2.sfc map hexmap.yaml out dump.txt
Remove every other byte since each letter is represented by two bytes:
$ ./reader.py mt2.sfc odd map hexmap.yaml out dump.txt
Line break at every 64 byte:
$ ./reader.py mt2.sfc map hexmap.yaml wrap 64 out dump.txt
Hex dump table:
$ ./reader.py mt2.sfc wrap 64 hexify out hexdump.txt
Labeled hex dump table:
$ ./reader.py mt2.sfc wrap 64 hexify label out hexdump.txt

>> rom = ROM(path='./mt2.sfc')
>> print(rom.hextable())
>> oddrom = rom.odd()
>> rom.save('./copy.sfc')
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read a ROM and process it.")
    parser.add_argument('infile', help="Path to the file to be read.")
    """ Encoding: The appearance of the characters themselves (hexadecimal, ASCII, etc.) """
    parser.add_argument('inencoding', choices=["bin", "hex"], help="Encoding of the read file.")
    parser.add_argument('--transliteration', '-t', nargs='+', help="YAML file mapping a set of symbols to another set of symbols.")
    parser.add_argument('process', nargs='*',
                        choices=["odd",  # [X] -> [X] : Strip away the 2nd, 4th, 6th... character.
                                 "hex",  # [Int] -> [String] : Show the values in hexadecimal.
                                 "text",  # [Int] -> [String] : Convert the values to UTF-8 characters.
                                 "map",  # [X] -> [Y] : Transliterate using the supplied file(s). The Nth time this filter is used, the Nth file is used.
                                 "replace",  # String -> String : Search/replace using the supplied file(s). The Nth time this filter is used, the Nth file is used.
                                 "pack",  # [String] -> [String] : Strip away whitespace.
                                 "join",  # [String] -> String : Join all the strings into one.
                                 "table",  # [String] -> String : Display the results in a table.
                                 "label",  # [String] -> [String] : Label each row with the address of its first element.
                                ],
                        help="Apply processing rules to the out-encoded stream.")
    parser.add_argument('--width', '-w', type=int, default=0, help="Number of columns in the output.")
    parser.add_argument('--outfile', '-o', help="Output to file instead of to console.")

    args = parser.parse_args()
    out = convert(args.infile, args.inencoding, args.process, args.width, args.transliteration)
    f = sys.stdout
    if args.outfile:
        f = open(args.outfile, 'w', encoding="utf8")
    print(out, file=f)
