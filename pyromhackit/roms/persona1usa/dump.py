#!/usr/bin/env python

import os
from pyromhackit.rom import ROM
import pyromhackit.thousandcurses.codec as codec
from pyromhackit.roms.persona1usa.hexmap import transliter

package_dir = os.path.dirname(os.path.abspath(__file__))

r = ROM(path=os.path.join(package_dir, "resources/copyrighted/TENSI.BIN"))

class Persona1Codec(codec.Decoder):
    def decode(bytestr):
        return "".join(transliter[bytestr[i:i+2]] for i in range(0, len(bytestr), 2))

r2 = r[25704*2:]
s = r2.decode(Persona1Codec)

print(s)