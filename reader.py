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
        row = stream[i:i+cols]
        table.add_row(row)
    return table

def compact(stream, cols):
    """ Output every character with nothing inbetween, making a line break every cols characters.
        If cols = 0, output everything on one line. """
    output = []
    for i in range(len(stream)):
        output.append(stream[i])
        if cols > 0 and i % cols == 0:
            output.append('\n')
    return "".join(output).strip()
    
def minimal(stream, cols):
    """ Same as compact(...), but also removes all whitespace. """
    output = compact(stream, cols)
    for s in string.whitespace.replace("\n", "").replace("\r", ""):
        output = output.replace(s, "")
    return output
    
def convert(infile, inencoding, outencoding, outformat, columns, transliterationfile):
    """ Uses the inencoding to read the infile, does some transliteration and outputs it in outencoding using outformat. """
    contents = readbin(infile)
    charmap = read_yaml(transliterationfile) if transliterationfile else dict()
    contents = [ord(charmap[b]) if b in charmap else b for b in contents]
    if outencoding == "hex":
        contents = [hex(n)[2:].upper() for n in contents]
    elif outencoding == "text":
        contents = [chr(n) for n in contents]
    if outformat == "table":
        output = tabulate(contents, columns)
    elif outformat == "compact":
        output = compact(contents, columns)
    elif outformat == "minimal":
        output = minimal(contents, columns)
    return output
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Translate one format to another format.")
    parser.add_argument('infile', help="Path to the file containing the hex.")
    parser.add_argument('inencoding', choices=["bin", "hex"], help="Encoding of the read file.")
    """ Encoding: The appearance of the characters themselves (hexadecimal, ASCII, etc.) """
    parser.add_argument('outencoding', choices=["hex", "text"], help="Encoding of the output.")
    """ Format: The way the individual characters are output (in a table, on one line, etc.) """
    parser.add_argument('outformat', choices=["table", "compact", "minimal"], help="Format of the output.")
    parser.add_argument('columns', type=int, help="Number of columns in the output.")
    parser.add_argument('--transliteration', '-t', help="YAML file mapping the read bytes into characters.")
    parser.add_argument('--outfile', '-o', help="Output to file instead of to console.")

    args = parser.parse_args()

    out = convert(args.infile, args.inencoding, args.outencoding, args.outformat, args.columns, args.transliteration)
    f = sys.stdout
    if args.outfile:
        f = open(args.outfile, 'w', encoding="utf8")
    print(out, file=f)
