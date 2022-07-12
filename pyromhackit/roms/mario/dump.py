#!/usr/bin/env python3

from pyromhackit.rom import ROM
from pyromhackit.semantics.rotating_monobyte.finder import RotatingMonobyteFinder

if __name__ == '__main__':
    rom = ROM("copyrighted/mario.nes")
    bs = bytes(rom)
    finder = RotatingMonobyteFinder()
    semantics = finder.find(bs)
    irom_string = ''.join(semantics.codec[b] for b in semantics.topology.structure(bs))
    print("Script mixed with data:")
    print(irom_string)
