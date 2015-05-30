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
    lines = filecontents(path)
    stream = open(path, 'r', encoding='utf8')
    dct = yaml.load(stream)
    return dct

def pretty_table(matrix, encoder=dict()):
    """ Readable representation of a list of lists, translating entries according to encoder. """
    if len(matrix) == 0:
        return u""
    table = PrettyTable(header=False, border=True, padding_width=0)
    for row in matrix:
        filteredrow = row[::2]
        encodedrow = tuple(encoder[x] if x in encoder else x for x in filteredrow)
        table.add_row(encodedrow)
    return str(table)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Translate hex -> letters.")
    parser.add_argument('file', help="Path to the file containing the hex.")
    parser.add_argument('--output', '-o', help="Output to file instead of to console.")
    args = parser.parse_args()

    lines = filecontents(args.file)
    hex = [line.split() for line in lines]
    hex = [tuple(int(s, 16) for s in row) for row in hex]
    hexmap = read_yaml('hexmap.yaml')
    table = pretty_table(hex, hexmap)
    f = sys.stdout
    if args.output:
        f = open(args.output, 'w', encoding="utf8")
    print(table, file=f)
