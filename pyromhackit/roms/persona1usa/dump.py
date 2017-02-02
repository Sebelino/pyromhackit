#!/usr/bin/env python

import os
from pyromhackit.rom import ROM, Morphism
import pyromhackit.thousandcurses.codec as codec
from pyromhackit.roms.persona1usa.hexmap import transliter

package_dir = os.path.dirname(os.path.abspath(__file__))

rom_path = os.path.join(package_dir, "resources/copyrighted/TENSI.BIN")

class Persona1Codec(codec.Decoder):
    def decode(bytestr):
        return "".join(transliter[bytestr[i:i+2]] for i in range(0, len(bytestr), 2))


if __name__ == '__main__':
    r = ROM(rom_path)

    r2 = r[25704*2:25704*2+100]
    f = Morphism(r2, Persona1Codec)

    print(r2)
    print()
    print(f)
