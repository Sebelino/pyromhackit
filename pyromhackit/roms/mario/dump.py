#!/usr/bin/env python3
from pyromhackit.gslice.plot import plot_selection
from pyromhackit.gslice.view import highlight_each_selection
from pyromhackit.rom import ROM
from pyromhackit.semantics.rotating_monobyte.finder import RotatingMonobyteFinder
from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier


def dump_rom(path: str):
    rom = ROM(path)
    bs = bytes(rom)
    finder = RotatingMonobyteFinder()
    semantics = finder.find(bs)
    irom_string = ''.join(semantics.codec[b] for b in semantics.topology.structure(bs))
    identifier = EnglishDictionaryBasedIdentifier()
    selection = identifier.str2selection(irom_string)
    print("Script:")
    print(selection.select(irom_string))
    highlight_each_selection(irom_string, selection, 10)
    plot_selection(selection)


if __name__ == '__main__':
    dump_rom("copyrighted/mario.nes")
