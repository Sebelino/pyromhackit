import json
from collections import namedtuple
from enum import Enum

import unicodedata
from typing import Union

import re
from bidict import bidict, KeyAndValueDuplicationError, OVERWRITE

from pyromhackit.rom import ROM
from pyromhackit.irom import IROM
from pyromhackit.thousandcurses.codec import Tree


class Hacker(object):
    """
    Assumes a one-to-one mapping between bytestring leaves and string leaves.
    Assumes dicts as decoders (and encoders!) instead of functions.
    """

    Behavior = Enum('Behavior', 'RAISE SWAP')

    def __init__(self, item: 'ROM'):
        if isinstance(item, ROM):
            self.src = item
        else:
            raise ValueError("Unexpected type: {}".format(type(item)))
        mu = self._any_codec()
        self.affection = lambda p: p  # Functions are simpler than dicts; avoids a mmap for large bidicts
        self.invaffection = self.affection  # ...but unfortunately requires an inverse function
        self.codec = mu  # Should probably support multiple codecs, assigning one codec to each subtree/leaf.
        self.codec_behavior = self.Behavior.SWAP
        self.dst = None
        self._compute_dst()
        self.visage = dict()  # Dict mapping each actual character into a presented character
        self.last_codec_path = None
        self.last_visage_path = None
        self.last_selection_path = None

    def _compute_dst(self):
        """ Uses the information in self.src, self.affection, and self.codec to update self.dst. """
        selection = self.src.selection() if self.dst else None
        self.src.reveal(None, None)
        self.dst = IROM(self.src, self.codec)
        if selection:
            self.coverup(None, None)
            for a, b in selection:
                self.reveal(a, b)
                #self.dst = self.dsttree.transliterate(self.codec)
                #self.dst = self.dsttree.restructured(self.affection)

    # TODO Requires Tree to be mutable. Could let srctree be immutable Tree and dsttree be MutableTree
    def _compute_leaf(self, dstleafpath):
        """ Using self.codec, updates the leaf in self.dsttree pointed to by the index path @dstleafpath. """
        self._compute_dst()
        #srcleafpath = self.affection.inv[dstleafpath]
        #srcleaf = self.srctree.reel_in(*srcleafpath)

    def _any_codec(self, occupied=dict()):
        mu = bidict()
        codepoint = 128
        categories = {'Ll', 'Lu', 'Lo'}
        for i in range(self.src.atomcount()):
            srcleaf = self.src.getatom(i)
            if srcleaf not in mu and srcleaf not in occupied:
                while chr(codepoint) in occupied.values() or unicodedata.category(chr(codepoint)) not in categories:
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
        self._compute_dst()

    def reverse_operate(self):
        child_count = max(p[0] for p in self.affection.values())
        newaffection = bidict()
        for srcleafpath in self.affection:
            dstleafpath = self.affection[srcleafpath]
            newidx = child_count - dstleafpath[0]
            newaffection[srcleafpath] = (newidx,) + dstleafpath[1:]
        self.affection = newaffection
        self._compute_dst()

    def persona_operate(self):
        # n-2 tree -> 2-n tree
        self.unzip_operate()
        self.reverse_operate()

    # Transliteration transformations preserve structure, so only self.codec is affected while self.affection is not
    # altered.
    def persona_transliterate(self):
        self.codec = self._persona_codec()
        self._compute_dst()

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
        return str(self.dst).translate(str.maketrans(self.visage))

    def clothe(self, actual_char, viewed_substring):
        """ Alter the presentation of certain characters. Not necessarily injective. """
        assert isinstance(actual_char, str)
        assert len(actual_char) >= 1
        if len(actual_char) >= 2:
            raise NotImplementedError("Support for multi-character keys in visage not implemented yet.")
        self.visage[actual_char] = viewed_substring

    def coverup(self, from_index: Union[int, None], to_index: Union[int, None]):
        self.src.coverup(from_index, to_index, virtual=True)
        self.dst.coverup(from_index, to_index, virtual=True)

    def reveal(self, from_index: Union[int, None], to_index: Union[int, None]):
        self.src.reveal(from_index, to_index)
        self.dst.reveal(from_index, to_index)

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
        """ Returns the (val+1)'th character if val is a number, or the corresponding substring if val is a slice. """
        if isinstance(val, int):
            return self.dst[val]
        if isinstance(val, slice):
            return self.dst[val]
        raise TypeError("IROM indices must be integers or slices, not {}".format(type(val).__name__))

    def _leafid(self, idx):
        """ Returns the ID of the leaf containing the character that has a string offset of @idx. """
        flat_tree = self.dst.flatten_without_joining()
        cumlength = 0
        for leafid in flat_tree:
            cumlength += len(self.dst[leafid])
            if idx < cumlength:
                return leafid
        assert len(flat_tree) >= 1, "Software fault"
        raise IndexError("Tree index out of range")

    def place(self, idx: int, value: str):  # TODO is this the same as set_destination_at? Or is that single-char?
        self[idx:idx + len(value)] = value

    def set_destination(self, dst1: str, dst2: str):
        """ Change all @dst1 string leaves into @dst2. """
        if self.codec_behavior == self.Behavior.RAISE:
            assert dst2 not in self.codec.inv, "String leaf {} already exists in the codec.".format(repr(dst2))
            src1 = self.codec.inv.pop(dst1)
            self.codec.inv[dst2] = src1
        elif self.codec_behavior == self.Behavior.SWAP:
            src1 = self.codec.inv.pop(dst1)
            if dst2 in self.codec.inv:
                src2 = self.codec.inv.pop(dst2)
                self.codec[src2] = dst1
            self.codec[src1] = dst2
        self._compute_dst()

    def set_destination_at(self, idx: int, dst: str):
        """ Set the @idx'th character in the destination string to @dst, updating the codec accordingly. """
        if self.dst[idx] == dst:
            return  # If the character is already set to @dst, do nothing
        dstatomidx = idx  # FIXME assumes IROM atom length = 1
        dstidx, _, dstidxpath, _, _ = self.dst.atomindex2entry(dstatomidx)
        assert dstidx == dstatomidx  # TODO
        srcidxpath = self.invaffection(dstidxpath)
        _, _, _, _, bs = self.src.indexpath2entry(srcidxpath)
        try:
            self.codec[bs] = dst
        except KeyAndValueDuplicationError as e:
            if self.codec_behavior == self.Behavior.SWAP:
                occupying_key = self.codec.inv[dst]
                swapped_value = self.codec[bs]
                self.codec.putall({(occupying_key, swapped_value), (bs, dst)}, on_dup_val=OVERWRITE)
            else:
                raise e
        self._compute_leaf(srcidxpath)

    def put(self, src: bytes, dst: str):
        """ For every ROM atom containing @src, updates the associated IROM atom so that it becomes equal to @dst. """
        assert isinstance(src, bytes), "Expected bytes, got: {}".format(type(src))
        assert isinstance(dst, bytes), "Expected string, got: {}".format(type(dst))
        self.codec[src] = dst
        self._compute_dst()

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

    def traverse_preorder(self):
        """ Returns a generator for tuples (a,b,c,d,e,f,g,h,i,j) where
        a is the virtual ROM byte index
        b is the (virtual) ROM atom index
        c is the (virtual) ROM atom index path
        d is the physical ROM byte index.
        e is the ROM atom content
        f is the IROM character index
        g is the IROM atom index
        h is the IROM atom index path
        i is the IROM encoded byte index
        j is the IROM atom content
        """
        Entry = namedtuple("Entry", ["vbyteindex", "vatomindex", "vatomindexpath", "pbyteindex", "ratom",
                                     "icharindex", "iatomindex", "iatomindexpath", "ibyteindex", "iatom"])
        for vbyteindex, vatomindex, vatomindexpath, pbyteindex, ratom in self.src.traverse_preorder():
            icharindex, iatomindex, iatomindexpath, ibyteindex, iatom = self.dst.atomindex2entry(vatomindex)
            yield Entry(vbyteindex, vatomindex, vatomindexpath, pbyteindex, ratom,
                        icharindex, iatomindex, iatomindexpath, ibyteindex, iatom)

    def dump(self, path):
        self.dst.dump(path)

    def dump_selection(self, json_path=None):
        """ Dump a list of interval lists [a, b] describing the revealed intervals to the JSON file with path
        @json_path. """
        if json_path is None:
            json_path = self.last_selection_path
        with open(json_path, 'w') as f:
            json.dump(list(self.dst.selection()), f, sort_keys=True, indent=4, separators=(',', ': '))
        self.last_selection_path = json_path

    def load_selection(self, json_path=None):
        """ Reveal only the sections of the ROM specified in the JSON file with path @json_path. """
        self.coverup(None, None)
        with open(json_path, 'r') as f:
            loaded = json.load(f)
            assert isinstance(loaded, list)
            for element in loaded:
                assert isinstance(element, list)
                a, b = element
                assert isinstance(a, int)
                assert isinstance(b, int)
                self.reveal(a, b)
        self.last_selection_path = json_path

    def load_selection_from_copy(self, path):
        """ File @path contains a string identical to the IROM except that zero or more substrings have been removed.
        The selections of the IROM and ROM is adjusted so that the substrings not present in @path become hidden.
        """
        self.dst.load_selection_from_copy(path)
        self.src.coverup(None, None)
        for a, b in self.dst.selection():
            self.src.reveal(a, b)

    def dump_codec(self, json_path=None):
        if json_path is None:
            json_path = self.last_codec_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'w') as f:
            json.dump({s: list(bs) for bs, s in self.codec.items()}, f, sort_keys=True, indent=4,
                      separators=(',', ': '))
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
            self._compute_dst()
            self.last_codec_path = json_path

    def dump_visage(self, json_path=None):
        if json_path is None:
            json_path = self.last_visage_path
        if not json_path:
            raise ValueError("Expected valid filename or path, got: {}".format(json_path))
        with open(json_path, 'w') as f:
            json.dump(self.visage, f, sort_keys=True, indent=4, separators=(',', ': '))
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

    def dump_view(self, path):
        with open(path, 'w') as f:
            f.write(self.show())

    def __str__(self):
        return self.show()
        #return str(self.dst)
        #classname = self.__class__.__name__
        #return "{}{}".format(classname, self.dsttree)

    def __len__(self):
        return len(self.src)

    def __deepcopy__(self, memodict={}):
        cpy = self.__class__(self.srctree)
        cpy.codec = self.codec
        cpy.dsttree = Tree(self.dsttree)
        cpy.set_codec_behavior(self.codec_behavior)
        return cpy

