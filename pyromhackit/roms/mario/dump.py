#!/usr/bin/env python3

from pyromhackit.gslice.view import highlight_each_selection
from pyromhackit.rom import ROM
from pyromhackit.semantics.rotating_monobyte.finder import RotatingMonobyteFinder
from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier

if __name__ == '__main__':
    rom = ROM("copyrighted/mario.nes")
    bs = bytes(rom)
    finder = RotatingMonobyteFinder()
    semantics = finder.find(bs)
    irom_string = ''.join(semantics.codec[b] for b in semantics.topology.structure(bs))
    tolerated_char_count = 0
    identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=tolerated_char_count)
    selection = identifier.str2selection(irom_string)
    print("Script:")
    print(selection.select(irom_string))
    highlight_each_selection(irom_string, selection, tolerated_char_count)
