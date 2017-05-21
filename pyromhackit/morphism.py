#!/usr/bin/env python

import difflib
import json
from typing import Union
from enum import Enum

import re
from bidict import bidict, KeyAndValueDuplicationError, OVERWRITE, IGNORE
from math import ceil
from prettytable import PrettyTable

from pyromhackit.rom import ROM
from pyromhackit.thousandcurses.codec import Tree


class Morphism(object):
    """ A ROM paired with a string decoded from it using a specific decoder. The decoded string is a 'facet'
     of the ROM -- if the ROM is modified, the decoded string is generally modified as well. On the other hand,
     the decoded string cannot be directly modified, as it is solely dependent on the ROM and on the decoder.
     Formally, a Morphism is a function from the set of ROMs (bytestrings) to the set of strings.
     Unlike with an Isomorphism, multiple different ROMs can be decoded into the same string. You want to use this
     class if you have only implemented a decoder and/or if you are only interested in knowing how the decoded string
     changes as you edit the ROM. A typical use case scenario would be to to dump the in-game script for your ROM. """

    def __init__(self, rom_specifier, decoder):
        self.src = ROM(rom_specifier)
        self.decoder = decoder
        self.srctree, self.dsttree, self.graph = decoder.correspondence(bytes(self.src))
        try:
            self.dst = decoder.decode(bytes(self.src))
        except:  # FIXME
            self.dst = self.dsttree.flatten()

    def index(self, item):
        """ If item is a bytestring, return (i, j) where i is the index of the first byte in item found in the
        ROM and j is the index of the first character in the decoded string that item affects.
        If item is a string, return (i, j) where j is the index of the first character in item found in the
        decoded string and i is the index of the first byte in the ROM that affects item.
        """
        if isinstance(item, bytes):
            i = self.src.index(item)
            (j,) = self.graph[(i,)]
            return i, j
        elif isinstance(item, str):
            j = self.dst.index(item)
            for bl in self.graph:
                vs = {v[0] for v in self.graph[bl]}
                if j in vs:
                    (i,) = bl
                    return i, j
            raise ValueError("Affecting byte not found.")
        raise TypeError("Argument must be either a bytestring or a string.")

    def source_diffusion(self, idx):
        """ Returns the set of indices of the characters in the decoded string affected when altering the ith byte
        in the ROM. """
        self.src[idx]  # Raise IndexError?
        indices = set()
        for i in range(2 ** 8):
            alteration = self.src[:idx] + bytes([i]) + self.src[idx + 1:]
            dalteration = self.decoder.decode(alteration)
            diff = difflib.ndiff(dalteration, self.dst)
            adiff = [ds for ds in diff if ds[0] != '+']
            for j, s in enumerate(adiff):
                if s[0] == '-':
                    indices.add(j)
        return indices

    def impose_character(self, byteidx, stridx, c):
        """ By modifying the byteidx'th byte, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """
        return None

    def impose_decoding(self, b, c):
        """ By modifying the way the decoder associates byte b to a character, find a decoder that associates
         b to character c. Return a new Morphism based on the altered decoder or None if no way to make such an
         alteration could be found. """
        newdecoder = self.decoder
        newdecoder[b] = c
        return Morphism(self.src, newdecoder)

    def dump(self, path):
        """ Dump the decoded string. """
        with open(path, 'w') as f:
            f.write(self.dst)

    def __getitem__(self, val):
        if isinstance(val, int):
            return self.src[val]
        if isinstance(val, slice):
            rom = self.src[val.start:val.stop:val.step]
            return Morphism(rom, self.decoder)
        raise TypeError("Morphism indices must be integers or slices, not {}".format(type(val).__name__))

    def __str__(self):
        romstr = str(self.src).replace(self.src.__class__.__name__, self.__class__.__name__, 1)
        whitespace = " " * (len(self.__class__.__name__) + 2)
        dststr = repr(self.dst)
        result = "{},\n{}{})".format(romstr[:-1], whitespace, dststr)
        return result


class Isomorphism(Morphism):
    """ A ROM paired with a string decoded from it using a specific codec. The decoded string is simply another
    way to represent the ROM -- if the ROM is modified, so is the decoded string. Conversely, if the decoded string
    is modified, so is the ROM. Formally, an Isomorphism is a bijective function from the set of ROMs (bytestrings)
    to the set of strings. You want to use this class if you want to be able to edit the underlying ROM by editing a
    more user-friendly decoding of it. A typical use case scenario is to edit in-game text."""

    def impose_byte(self, stridx, byteidx, b):
        """ By modifying the stridx'th character, find a byte value that causes the stridx'th character
        to become character c. Return None if no such value exists. """
        return None


Behavior = Enum('Behavior', 'RAISE SWAP')


class IROM(object):
    """
    Isomorphism of a ROM.
    Assumes a one-to-one mapping between bytestring leaves and string leaves.
    Assumes dicts as decoders (and encoders!) instead of functions.
    """

    def __init__(self, item):
        if isinstance(item, ROM):
            self.srctree = Tree(item.content.list())
        elif isinstance(item, Tree):
            self.srctree = item
        else:
            raise ValueError("Unexpected type: {}".format(type(item)))
        mu = self._any_codec()
        self.affection = bidict({(p, p) for p in self.srctree.leaf_indices()})
        self.codec = mu  # Should probably support multiple codecs, assigning one codec to each subtree/leaf.
        self.codec_behavior = Behavior.SWAP
        self._compute_dsttree()
        self.visage = dict()  # Dict mapping each actual character into a presented character
        self.last_codec_path = None
        self.last_visage_path = None

    # Uses the information in self.srctree, self.affection, and self.codecs to update self.dsttree.
    def _compute_dsttree(self):
        self.dsttree = self.srctree
        self.dsttree = self.dsttree.transliterate(self.codec)
        self.dsttree = self.dsttree.restructured(self.affection)

    # TODO Requires Tree to be mutable. Could let srctree be immutable Tree and dsttree be MutableTree
    def _compute_leaf(self, dstleafpath):
        """ Using self.codec, updates the leaf in self.dsttree pointed to by the index path @dstleafpath. """
        self._compute_dsttree()
        #srcleafpath = self.affection.inv[dstleafpath]
        #srcleaf = self.srctree.reel_in(*srcleafpath)

    def _any_codec(self, occupied=dict()):
        mu = bidict()
        codepoint = 128
        for srcleaf in self.srctree.flatten_without_joining():
            if srcleaf not in mu and srcleaf not in occupied:
                while chr(codepoint) in occupied.values():
                    codepoint += 1
                mu[srcleaf] = chr(codepoint)
                codepoint += 1
        return mu

    def _ascii_codec(self):
        mu = bidict((bytes([b]), chr(b)) for b in bytes(range(2**8)))
        return mu

    # Operation transformations modify only structure, so only self.affection is affected while self.dsttree can be
    # automatically computed afterwards.
    def unzip_operate(self):
        # n-m tree -> m-n tree
        old_affection = self.affection
        self.affection = bidict()
        for p1 in old_affection:
            p2 = old_affection[p1]
            p2new = tuple(reversed(p2))
            self.affection[p1] = p2new
        self._compute_dsttree()

    def reverse_operate(self):
        child_count = max(p[0] for p in self.affection.values())
        newaffection = bidict()
        for srcleafpath in self.affection:
            dstleafpath = self.affection[srcleafpath]
            newidx = child_count - dstleafpath[0]
            newaffection[srcleafpath] = (newidx,) + dstleafpath[1:]
        self.affection = newaffection
        self._compute_dsttree()

    def persona_operate(self):
        # n-2 tree -> 2-n tree
        self.unzip_operate()
        self.reverse_operate()

    # Transliteration transformations preserve structure, so only self.codec is affected while self.affection is not
    # altered.
    def persona_transliterate(self):
        self.codec = self._persona_codec()
        self._compute_dsttree()

    def _persona_codec(self):
        mu = bidict()
        for i in range(2**8):
            mu[bytes([i])] = chr(2**9+i)
        mu[bytes([0])] = " "  # 0
        for i in range(ord('z')-ord('a')+1):  # 1-26
            mu[bytes([i+0x01])] = chr(ord('a')+i)
        for i in range(ord('z')-ord('a')+1):  # 224-249
            mu[bytes([i+0xe0])] = chr(ord('A')+i)
        return mu

    def set_codec_behavior(self, behavior):
        self.codec_behavior = behavior

    def show(self, start=0, stop=None):
        if start != 0 or stop:
            raise NotImplementedError()
        return str(self).translate(str.maketrans(self.visage))

    def clothe(self, actual_char, viewed_substring):
        """ Alter the presentation of certain characters. Not necessarily injective. """
        assert isinstance(actual_char, str)
        assert len(actual_char) >= 1
        if len(actual_char) >= 2:
            raise NotImplementedError("Support for multi-character keys in visage not implemented yet.")
        self.visage[actual_char] = viewed_substring

    def coverup(self, from_index: Union[int, None], to_index: Union[int, None]):
        raise NotImplementedError()

    def reveal(self, from_index: Union[int, None], to_index: Union[int, None]):
        raise NotImplementedError()

    def character_diffusion(self, charindex):
        """ Returns the set or slice of indices of the bytes in the ROM affected when altering the ith character in the
        decoded string. """
        charleafid = self._leafid(charindex)
        byteleafid = self.affection[charleafid]
        # TODO: Inefficient
        cumlength = 0
        for leafpath in self.srctree.leaf_indices():
            current_leafid = self.srctree.reel_in(*leafpath)
            current_length = len(self.src[current_leafid])
            if current_leafid == byteleafid:
                return slice(cumlength, cumlength + current_length)
            cumlength += current_length
        raise RuntimeError("Diffusion for index {} not found".format(charindex))

    def __getitem__(self, val):
        """ Returns the (val+1)'th character if val is a number, or the corresponding substring substring if val is a
        slice. """
        dststr = self.dsttree.flatten()
        if isinstance(val, int):
            return dststr[val]
        if isinstance(val, slice):
            return dststr[val]
        raise TypeError("IROM indices must be integers or slices, not {}".format(type(val).__name__))

    def _leafid(self, idx):
        """ Returns the ID of the leaf containing the character that has a string offset of @idx. """
        flat_tree = self.dsttree.flatten_without_joining()
        cumlength = 0
        for leafid in flat_tree:
            cumlength += len(self.dst[leafid])
            if idx < cumlength:
                return leafid
        assert len(flat_tree) >= 1, "Software fault"
        raise IndexError("Tree index out of range")

    def find(self, *args):
        return self.dsttree.flatten().find(*args)

    def finditer(self, pattern):
        """ Returns an ordered list of matches with span=(a, b) such that self[a:b] matches @pattern. """
        return re.finditer(pattern, self.dsttree.flatten())

    def first_match(self, pattern):
        """ Return the first match for the given pattern. """
        return next(self.finditer(pattern))

    def first_group(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).group(1)

    def first_group_index(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).start(1)

    def grep(self, pattern, context=50, labels=True):
        for m in self.finditer(pattern):
            s = m.string[m.start() - context:m.end() + context]
            label = ""
            if labels:
                label = "{}: ".format(hex(m.start()))
            print("{}{}".format(label, s))

    def place(self, idx, value):
        self[idx:idx + len(value)] = value

    def set_destination(self, dst1: str, dst2: str):
        """ Change all @dst1 string leaves into @dst2. """
        if self.codec_behavior == Behavior.RAISE:
            assert dst2 not in self.codec.inv, "String leaf {} already exists in the codec.".format(repr(dst2))
            src1 = self.codec.inv.pop(dst1)
            self.codec.inv[dst2] = src1
        elif self.codec_behavior == Behavior.SWAP:
            src1 = self.codec.inv.pop(dst1)
            if dst2 in self.codec.inv:
                src2 = self.codec.inv.pop(dst2)
                self.codec[src2] = dst1
            self.codec[src1] = dst2
        self._compute_dsttree()

    def set_destination_at(self, idx: int, dst: str):
        """ Set the @idx'th character in the destination string to @dst. """
        # Propagate to src
        dstleafpath = self.dsttree.get_leaf_path(idx)
        srcleafpath = self.affection.inv[dstleafpath]
        bs = self.srctree.reel_in(*srcleafpath)
        try:
            self.codec[bs] = dst
        except KeyAndValueDuplicationError as e:
            if self.codec_behavior == Behavior.SWAP:
                occupying_key = self.codec.inv[dst]
                swapped_value = self.codec[bs]
                self.codec.putall({(occupying_key, swapped_value), (bs, dst)}, on_dup_val=OVERWRITE)
            else:
                raise e
        self._compute_leaf(srcleafpath)

    def put(self, src: bytes, dst: str):
        self.codec[src] = dst
        self._compute_dsttree()

    def putall(self, items):
        for src, dst in items:
            self.put(src, dst)

    def __setitem__(self, key, value):
        # Modifies self.codec and, by implication, self.dsttree and self.srctree
        if isinstance(key, str) and len(key) == 1 and isinstance(value, str):
            self.set_destination(key, value)
        elif isinstance(key, int):
            self.set_destination_at(key, value)
        elif isinstance(key, slice):
            for i, v in zip(range(key.start, key.stop), value):
                self.set_destination_at(i, v)
        elif isinstance(key, bytes) and isinstance(value, str):
            self.put(key, value)
        else:
            raise NotImplementedError()

    def undo(self):
        """ Resets the last operation that affected self.codec self.codec. """
        raise NotImplementedError()

    def replace_regex(self, regex: str, replacement: str):
        m = re.search(regex, self[:])
        for groupidx in range(1, len(m.groups()) + 1):
            a, b = m.span(groupidx)
            substring = self[a:b]
            subreplacement = replacement[a - m.start():b - m.end()]
            assert len(substring) == len(subreplacement)  # TODO Decide what to do with this
            self.set_destination(substring, subreplacement)

    def flatten(self):
        return self.dsttree.flatten()

    def dump_codec(self, json_path=None):
        if json_path is None:
            json_path = self.last_codec_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'w') as f:
            json.dump({s: list(bs) for bs, s in self.codec.items()}, f)
            self.last_codec_path = json_path

    def load_codec(self, json_path=None, totality=False):
        """ Load the codec from the JSON file (stored as in inverted dict). If totality is True and there is a leaf in
        the ROM that the codec cannot decode, raise KeyError. Otherwise, map those leaves to unspecified strings. """
        if json_path is None:
            json_path = self.last_codec_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'r') as f:
            loaded = json.load(f)
            loaded = bidict({bytes(bs): s for s, bs in loaded.items()})
            self.codec = loaded
            if not totality:
                base = self._any_codec(loaded)
                self.codec.putall(base)
            self._compute_dsttree()
            self.last_codec_path = json_path

    def dump_visage(self, json_path=None):
        if json_path is None:
            json_path = self.last_visage_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'w') as f:
            json.dump(self.visage, f)
            self.last_visage_path = json_path

    def load_visage(self, json_path=None):
        if json_path is None:
            json_path = self.last_visage_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'r') as f:
            d = json.load(f)
            self.visage = d
            self.last_visage_path = json_path

    def table(self, cols=16, label=True, border=True, padding=1):
        """ Display the stream of characters in a table. """
        fields = [''] + [hex(i)[2:] for i in range(cols)]
        table = PrettyTable(field_names=fields, header=True, border=border, padding_width=padding)
        content = self.flatten()
        labelwidth = len(str(len(content)))
        for i in range(0, len(content), cols):
            segment = content[i:i + cols]
            segment = segment + " " * max(0, cols - len(segment))
            segment = list(segment)
            if label:
                fmtstr = "{:>" + str(labelwidth) + "}: "
                segment = [fmtstr.format(hex(i)[2:])] + segment
            table.add_row(segment)
        return table

    def grep_table(self, searchstring, context=3, cols=16, label=True, border=True, padding=1):
        s = self.dsttree.flatten()
        idx = s.index(searchstring)
        tbl = self.table(cols, label, border, padding)
        arow = int(idx / cols) - context
        brow = int(idx / cols) + ceil(len(searchstring) / cols) + context
        return tbl[arow:brow]

    def __str__(self):
        return self[:]
        #classname = self.__class__.__name__
        #return "{}{}".format(classname, self.dsttree)

    def __len__(self):
        return len(self.flatten())

    def __deepcopy__(self, memodict={}):
        cpy = self.__class__(self.srctree)
        cpy.codec = self.codec
        cpy.dsttree = Tree(self.dsttree)
        cpy.set_codec_behavior(self.codec_behavior)
        return cpy

