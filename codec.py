#!/usr/bin/env python

"""
Encoding/decoding functions.

An encoding function maps a bytestring to a unicode string.
A decoding function maps a unicode string to a bytestring.

Encoders/decoders are bijective -- each encoder has a inverse decoder function,
and vice versa.
"""


def hexify(bytestr):
    return "".join(("0"+hex(n)[2:])[-2:].upper() for n in bytestr)


def lame_decode(bytestr):
    """ To decode is to convert data from one format to another in a way such
    that its meaning becomes clearer. """
    alphabet = ["å", "ä", "ö"]
    return "".join(alphabet[b % 3] for b in bytestr)
