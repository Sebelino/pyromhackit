#!/usr/bin/env python

"""
Encoding/decoding functions.

An encoding function maps a bytestring to a unicode string.
A decoding function maps a unicode string to a bytestring.

Encoders/decoders are bijective -- each encoder has a inverse decoder function,
and vice versa.
"""

from abc import ABC, abstractmethod


class Codec(ABC):
    @abstractmethod
    def encode(bytestr):
        pass

    @abstractmethod
    def decode(string):
        pass


class Hexify(Codec):
    def encode(bytestr):
        raise NotImplementedError

    def decode(bytestr):
        return "".join(("0"+hex(n)[2:])[-2:].upper() for n in bytestr)


class MajinTenseiII(Codec):
    def encode(bytestr):
        raise NotImplementedError

    def decode(bytestr):
        idx = ord("0")
        garbage = [chr(i) for i in range(idx, idx+2**8)]
        jpidx = ord("あ")
        japanese = [chr(i) for i in range(jpidx, jpidx+2**8)]
        head = "".join(garbage[b] for b in bytestr[1::2])
        tail = "".join(japanese[b] for b in bytestr[::2])
        return head+tail
