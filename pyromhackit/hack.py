#!/usr/bin/env python

"""
Contains a bunch of atomic hacks in the form of functions, e.g.:
* "remove the Japanese from the naming screen"
* "translate opening sequence"
* "translate top menu element"
* "translate dialog box 234"

Usage:
$ python hacks.py (-t HACK1 [PARAM1 [PARAM2 [...]]])*

Do the examples above:
$ python hacks.py -t namingscreen topmenu dialog 234 > hack.ips
Translate text in all dialog files:
$ python hacks.py dialog all > hack.ips
Translate everything:
$ python hacks.py all > hack.ips

"""

from struct import pack

# TODO Move this to another file
def ips(records):
    recordstrings = [pack('>I',adr)[-3:]+pack('>I',len(records[adr]))[-2:]+records[adr] for adr in records]
    return b"PATCH"+b"".join(recordstrings)+b"EOF"

def sebepresents():
    records = {
        0x2F02B2: bytes([0x00,0,0x1D,0,0x0F,0,0x0C,0,0x0F]),  # "_ S E B E"
    }
    ipsstr = ips(records)
    with open('mt2.ips','wb') as f:
        f.write(ipsstr)

if __name__ == '__main__':
    sebepresents()
