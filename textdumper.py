#!/usr/bin/env python3.4

import argparse
import yaml
import sys
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
    bytes = []
    with open(path, 'rb') as f:
        bytestring = f.read(1)
        while bytestring != b"":
            byte = bytestring[0]
            bytes.append(byte)
            bytestring = f.read(1)
    return bytes

def tabulate(stream, cols):
    table = PrettyTable(header=False, border=True, padding=0)
    for i in range(0, len(stream), cols):
        row = stream[i:i+cols]
        table.add_row(row)
    return table

def convert(infile, informat, outformat, transliterationfile):
    contents = readbin(infile)
    charmap = read_yaml(transliterationfile) if transliterationfile else dict()
    contents = [ord(charmap[b]) if b in charmap else b for b in contents]
    if outformat == "hex":
        contents = [hex(n)[2:].upper() for n in contents]
    elif outformat == "text":
        contents = [chr(n) for n in contents]
    output = tabulate(contents, 16)
    return output
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Translate one format to another format.")
    parser.add_argument('infile', help="Path to the file containing the hex.")
    parser.add_argument('informat', choices=["bin", "hex"], help="Format of the read file.")
    parser.add_argument('outformat', choices=["hex", "text"], help="Format of the output.")
    parser.add_argument('--transliteration', '-t', help="YAML file mapping the read bytes into characters.")
    parser.add_argument('--outfile', '-o', help="Output to file instead of to console.")

    args = parser.parse_args()

    out = convert(args.infile, args.informat, args.outformat, args.transliteration)
    f = sys.stdout
    if args.outfile:
        f = open(args.outfile, 'w', encoding="utf8")
    print(out, file=f)
