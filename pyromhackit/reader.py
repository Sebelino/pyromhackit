#!/usr/bin/env python

import argparse
import yaml
import sys
import string
from prettytable import PrettyTable
import re
from ast import literal_eval

"""
Command-line interface for operating on ROMs.
"""


def filecontents(path):
    """ List of lines in a file specified by path. """
    with open(path, 'r', encoding='utf8') as f:
        content = f.readlines()
        return content


def read_yaml(path):
    """ YAML -> Dictionary. """
    # TODO duplicate in thousand-curses
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct


def readbin(path):
    """ Read the specified file into a byte array (integers). """
    f = open(path, 'rb')
    bytes = list(f.read())
    return bytes


def compact(stream, cols):
    """ Output every character with nothing in-between, making a line break
    every cols characters.  If cols = 0, output everything on one line. """
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
    """ Uses the inencoding to read the infile, does some transliteration and
    applies a sequence of additional processing filters. """
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
        return [("%06x: " % i).upper()+stream[i]
                if i % width == 0 else stream[i] for i in range(len(stream))]
    pipe = {
        "hex": ([int], [str], lambda lst: [("0"+hex(n)[2:])[-2:].upper()
                                           for n in lst]),
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
            raise Exception("Filter %s expected type %s, got %s"
                            % (filter, inputtype, contenttype))
        contents = operation(contents)
        if outputtype is not None:
            contenttype = outputtype
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


def bytes2hex(bytestr):
    """ Bytestring -> [String] """
    return [("0"+hex(b)[2:])[-2:].upper() for b in bytestr]


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
    """ Encoding: The appearance of the characters themselves (hexadecimal,
    ASCII, etc.) """
    parser.add_argument('inencoding', choices=["bin", "hex"],
                        help="Encoding of the read file.")
    parser.add_argument('--transliteration', '-t', nargs='+',
                        help="YAML file mapping a set of symbols to another"
                        " set of symbols.")
    parser.add_argument('process', nargs='*', choices=[
        "odd",  # [X] -> [X] : Strip away the 2nd, 4th, 6th... character.
        "hex",  # [Int] -> [String] : Show the values in hexadecimal.
        "text",  # [Int] -> [String] : Convert the values to UTF-8 characters.
        "map",  # [X] -> [Y] : Transliterate using the supplied file(s).
                # The Nth time this filter is used, the Nth file is used.
        "replace",  # String -> String : Search/replace using the supplied
                    # file(s). The Nth time this filter is used, the Nth file
                    # is used.
        "pack",  # [String] -> [String] : Strip away whitespace.
        "join",  # [String] -> String : Join all the strings into one.
        "table",  # [String] -> String : Display the results in a table.
        "label",  # [String] -> [String] : Label each row with the address of
                  # its first element.
        ],
        help="Apply processing rules to the out-encoded stream.")
    parser.add_argument('--width', '-w', type=int, default=0,
                        help="Number of columns in the output.")
    parser.add_argument('--outfile', '-o',
                        help="Output to file instead of to console.")

    args = parser.parse_args()
    out = convert(args.infile, args.inencoding, args.process, args.width,
                  args.transliteration)
    f = sys.stdout
    if args.outfile:
        f = open(args.outfile, 'w', encoding="utf8")
    print(out, file=f)
