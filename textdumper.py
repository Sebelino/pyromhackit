#!/usr/bin/env python3.4

import argparse
import pdb

def filecontents(path):
    with open(path) as f:
        content = f.readlines()
        return content

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Translate hex -> letters.")
    parser.add_argument('file', help="Path to the file containing the hex.")
    args = parser.parse_args()

    lines = filecontents(args.file)
    hex = [line.split() for line in lines]
    hex = [[int(s, 16) for s in row] for row in hex]
    for row in hex:
        print(" ".join([str(n) for n in row]))
