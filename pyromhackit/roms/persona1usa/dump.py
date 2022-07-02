#!/usr/bin/env python

import os
import random

import unicodedata

from pyromhackit.rom import ROM
from pyromhackit.hacker import Hacker, Behavior
import pyromhackit.thousandcurses.codec as codec
from pyromhackit.topology.tree import SimpleTopology
from pyromhackit.roms.persona1usa.hexmap import transliter
from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier

package_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(package_dir, "resources/paths.txt")) as f:
    sources_paths = f.read().strip().split()

sources = {path: dict() for path in sources_paths}

try:
    os.makedirs("output")
except FileExistsError:
    pass

persona_codec_path = "resources/persona_codec.json"
persona_visage_path = "resources/persona_visage.json"

for infile, outfiles in sources.items():
    outfiles["codec"] = persona_codec_path
    outfiles["visage"] = persona_visage_path
    outfiles["selection"] = os.path.join("resources", "{}.sel.json".format(os.path.basename(infile).lower()))
    outfiles["irom"] = os.path.join("output", "{}.irom.txt".format(os.path.basename(infile).lower()))
    outfiles["view"] = os.path.join("output", "{}.view.txt".format(os.path.basename(infile).lower()))


class Archive(object):  # File that can be unzipped into one or more ROMs.
    pass


class Persona1Codec(codec.Codec):
    @classmethod
    def domain(cls, bytestr: bytes):
        return codec.Tree([bytestr[i:i + 2] for i in range(0, len(bytestr), 2)])

    @classmethod
    def decode(cls, btree: codec.Tree):
        return btree.transliterate(transliter)


def any_lo_char():
    return any_lo_char.los_chars[random.randint(0, len(any_lo_char.los_chars))]


any_lo_char.los_chars = [chr(i) for i in range(2 ** 16) if unicodedata.category(chr(i)) == 'Lo']


def g(bytetreeish):
    return bytetreeish[1] if bytetreeish[0] == '0' else bytetreeish[1].decode()


def f(bytetreeish):
    return ['['] + reversed(g(c) for c in bytetreeish) + [']']


def persona1usa_structure(bs):
    return [[bs[i:i + 1], bs[i + 1:i + 2]] for i in range(0, len(bs), 2)]


def two_byte_structure(bs):
    return [bs[i:i + 2] for i in range(0, len(bs), 2)]


def hack(path, outfiles):
    import time; t = time.time()
    r = ROM(path, structure=SimpleTopology(2))
    #print("Created ROM: {}".format(time.time() - t))
    hacker = Hacker(r)
    #print("Created Hacker: {}".format(time.time() - t))
    hacker.load_codec(outfiles["codec"])
    #print("Loaded codec: {}".format(time.time() - t))
    hacker.load_visage(outfiles["visage"])
    #print("Loaded visage: {}".format(time.time() - t))
    try:
        hacker.load_selection(outfiles["selection"])
        print("Loaded selection: {}".format(time.time() - t))
    except FileNotFoundError:
        pass
    hacker.set_codec_behavior(Behavior.RAISE)
    return hacker


def dump_iroms_and_views():
    print("Dumping views for {} files...".format(len(sources)))
    for iterationno, (infile, outfiles) in enumerate(sources.items()):
        print("({}/{})".format(iterationno + 1, len(sources)), end=" ")
        if 'view' in outfiles and os.path.exists(outfiles['view']):
            print("Skipping {}".format(infile))
            continue
        print("Hacking {}".format(infile))
        hacker = hack(infile, outfiles)
        #hacker[chr(9166)] = '\n'
        hacker.dump(outfiles["irom"])
        hacker.dump_view(outfiles["view"])
        # hacker.reveal(None, None); hacker.load_selection_from_copy('e2dump.txt')


def dump_selections():
    for iterationno, (infile, outfiles) in enumerate(sources.items()):
        print("({}/{})".format(iterationno + 1, len(sources)), end=" ")
        if 'selection' in outfiles and os.path.exists(outfiles['selection']):
            print("Skipping {}".format(infile))
            continue
        print("Dumping selection for {}".format(infile))
        import time; t = time.time()
        hacker = hack(infile, outfiles)
        #hacker[chr(9166)] = '\n'
        sel = EnglishDictionaryBasedIdentifier(tolerated_char_count=15).str2selection(str(hacker.dst))
        hacker.set_selection(sel)
        hacker.dump_selection(outfiles["selection"])
        print("Elapsed: {}".format(time.time() - t))


if __name__ == '__main__':
    dump_selections()
    dump_iroms_and_views()

    #infile = "resources/copyrighted/psp_game/usrdir/pack/dng/d01/d01.bin"
    #hacker = hack(infile, sources[infile])



# Decoding function:
# 1. Totality. True iff the domain of definition equals the domain of discourse (the set of all bytestrings).
# 2. Surjection. True iff the image equals the codomain (the set of all strings).
# 3. Injection. True iff no two bytestrings map to the same string.
# 4. Functionality. True always since every bytestring maps to at most one string.
# Affection relation:
# 1. Left-totality.
# 2. Right-totality.
# 3. Left-uniqueness.
# 4. Right-uniqueness.

# <Bytestring> ::= {<Unit>}
# <Unit> ::= <Mod><Alpha>
# <Mod> ::= 0 | 1
#
#   b'0a1b1c0d1E'
# -> [[b'0', b'a'], [b'1', b'b'], [b'1', b'c'], [b'0', b'd'], [b'1', b'E']]
# -> f([[b'0', b'a'], [b'1', b'b'], [b'1', b'c'], [b'0', b'd'], [b'1', b'E']])
# == ['[', g([b'1', b'E']), g([b'0', b'd']), g([b'1', b'c']), g([b'1', b'b']), g([b'0', b'a']), ']']:[None, (4,), (3,), (2,), (1,), (0,), None]
# == ['[', 'E ', 'd', 'C', 'B', 'a', ']']:[None, (4,), (3,), (2,), (1,), (0,), None]
# -> '[EdCBa]'

# High-level properties:
# 1. Totality. NOT maintained since e.g. b'2c' and b'0a1' are not part of the grammar.
# 2. Surjection. NOT maintained since e.g. '+' is not part of the image.
# 3. Injection. NOT maintained since b'1a' and b'1A' both map to 'A'.
# Tree-level properties:
# 1. Left-totality. Even though no bytestring leaf is mapped, each leaf has an ancestor (here, parent) that is.
# 2. Right-totality NOT retained since the square bracket string nodes are not affected by anything.
# 3. Left-uniqueness since no two bytestring nodes affect the same string node.
# 4. Right-uniqueness since every bytestring leaf affects at most one string node.


# b'0a1b1c0d1E'
# -> [b'0a1b1c0d1E']
# -> f([b'0a1b1c0d1E'])
# == ['[', 'EdCBa', ']']:[None, (0,), None]
# -> '[EdCBa]'

# High-level properties:
# 1. Totality. NOT maintained since e.g. b'2c' and b'0a1' are not part of the grammar.
# 2. Surjection. NOT maintained since e.g. '+' is not part of the image.
# 3. Injection. NOT maintained since b'1a' and b'1A' both map to 'A'.
# Tree-level properties:
# 1. Left-totality. There is precisely one bytestring leaf and it affects to the middle string leaf.
# 2. Right-totality NOT retained since the square bracket string nodes are not affected by anything.
# 3. Left-uniqueness since no two bytestring nodes affect the same string node.
# 4. Right-uniqueness since the bytestring leaf affects at most one string node.


# <Bytestring> ::= {<Unit>}
# <Unit> ::= <Mod><Alpha>
# <Mod> ::= 0 | 1
#
# b'0a1b1c0d1E'
# -> [[b'0', b'a'], [b'1', b'b'], [b'1', b'c'], [b'0', b'd'], [b'1', b'E']]
# -> f([[b'0', b'a'], [b'1', b'b'], [b'1', b'c'], [b'0', b'd'], [b'1', b'E']])
# == ['[', g([b'1', b'E']), g([b'0', b'd']), g([b'1', b'c']), g([b'1', b'b']), g([b'0', b'a']), ']']:[None, (4,), (3,), (2,), (1,), (0,), None]
# == ['[', 'e ', 'd', 'C', 'B', 'a', ']']:[None, (4,), (3,), (2,), (1,), (0,), None]
# -> '[edCBa]'

# High-level properties:
# 1. Totality. NOT maintained since e.g. b'2c' and b'0a1' are not part of the grammar.
# 2. Surjection. NOT maintained since e.g. '+' is not part of the image.
# 3. Injection. NOT maintained since b'1a' and b'0A' both map to 'A'.
# Tree-level properties:
# 1. Left-totality. Even though no bytestring leaf is mapped, each leaf has an ancestor (here, parent) that is.
# 2. Right-totality NOT retained since the square bracket string nodes are not affected by anything.
# 3. Left-uniqueness since no two bytestring nodes affect the same string node.
# 4. Right-uniqueness since every bytestring leaf affects at most one string node.


# Want to construct a function M : ByteTree -> StringTree, Relation
# Base case:
# Tree whose all children are leaves
# Inductive case:
# Tree where at least one child is a tree
