#!/usr/bin/env python3.4

import argparse
import yaml
import sys
import string
from prettytable import PrettyTable
from pdb import set_trace

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

def tabulate(stream, cols):
    """ Display the stream of characters in a table. """
    table = PrettyTable(header=False, border=True, padding=0)
    for i in range(0, len(stream), cols):
        segment = stream[i:i+cols]
        row = segment+[" "]*max(0, cols-len(segment))
        table.add_row(row)
    return table

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

def convert(infile, inencoding, pipeline, width, transliterationfile):
    """ Uses the inencoding to read the infile, does some transliteration and applies a sequence of additional processing filters. """
    contents = readbin(infile)
    charmap = read_yaml(transliterationfile) if transliterationfile else dict()
    contents = [ord(charmap[b]) if b in charmap else b for b in contents]
    contenttype = [int]
    pipe = {
        "hex": ([int], [str], lambda lst: [("0"+hex(n)[2:])[-2:].upper() for n in lst]),
        "text": ([int], [str], lambda lst: [chr(n) for n in lst]),
        "odd": (None, None, lambda lst: lst[::2]),
        "table": (None, str, lambda lst: tabulate(lst, width)),
        "pack": ([str], str, pack),
    }
    for filter in pipeline:
        (inputtype, outputtype, f) = pipe[filter]
        if inputtype not in [None,contenttype]:
            raise Exception("Filter %s expected type %s, got %s" % (filter, inputtype, contenttype))
        contents = f(contents)
        if outputtype is not None: contenttype = outputtype
    if isinstance(contents, list):  # If still a list, make it into a string
        contents = compact(contents, width)
    return contents
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Translate one format to another format.")
    parser.add_argument('infile', help="Path to the file containing the hex.")
    """ Encoding: The appearance of the characters themselves (hexadecimal, ASCII, etc.) """
    parser.add_argument('inencoding', choices=["bin", "hex"], help="Encoding of the read file.")
    parser.add_argument('--transliteration', '-t', help="YAML file mapping the read bytes into characters.")
    parser.add_argument('process', nargs='*',
                        choices=["odd",  # [X] -> [X] : Strip away the 2nd, 4th, 6th... character
                                 "hex",  # [Int] -> [String] : Show the values in hexadecimal
                                 "text",  # [Int] -> [String] : Convert the values to UTF-8 characters
                                 "pack",  # [String] -> [String] : Strip away whitespace
                                 "table",  # [String] -> String : Display the results in a table
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
