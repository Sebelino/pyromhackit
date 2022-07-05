# Glossary

## ROM

A ROM (Read-only memory) -- in the context of this ROM-hacking library -- is an object holding a
read-only sequence of bytes. This source of this sequence may be a file, or simply a raw bytestring.
Since byte sequences loaded from a file tend to be large, and you may only be interested in a small
portion of the file, you have the option of ignoring arbitrary sections of the file.
In addition, you may define a hierarchical structure on the ROM. A common structure is the two-byte
structure, where the ROM is divided into a sequence of items where each item is a bytestring of
length 2. We may call each leaf in such a bytestring tree a ROM atom.

## ROM script

Each byte in a ROM belongs either to the _ROM's script_ or the _ROM's nonscript_.
A byte is said to belong to the ROM's script if it is used to encode the text stored in the ROM.
Loosely speaking, the ROM's script is the part of the ROM that we could be interested in dumping or editing.

## ROM nonscript

The part of a ROM that is not the ROM's script.
This includes stuff like assembly code, image data, etc.

## Topology
A ROM topology is a function that
takes a bytestring and outputs a tree
in which each leaf is bytestring
and each non-leaf is a function which takes
its children as input.
The evaluation of the tree's root node
is equal to the supplied bytestring.

For example, consider an ISO file containing
three files: TENSI.BIN, GAKI.BIN, WORM.BIN.
Each of the BIN files contains
text stored with two bytes per character.
A suitable topology is one which takes the
bytestring as input and outputs a tree with
the following properties:
* The root node of the tree is a function
which extracts the ISO.
* Each of its three child
nodes is a concatenation function.
* Each of the three children has child nodes
which are all leaves.
* Each leaf consist of a bytestring of length 2.

## Codec
A bijective dictionary mapping a character
to a bytestring.

## Semantics
A ROM semantics is a _topology_ paired with a _codec_.

## IROMs

An IROM (Isomorphism of a ROM) is an alternative way to represent a ROM, intended to be more
readable. An IROM instance is created from a ROM instance and provides a way to construct a semantics
for the ROM's content.
An IROM instance consists of a ROM, paired with a tree of strings such that there is
a codec -- a one-to-one correspondence -- between each ROM atom and each string leaf.
In an IROM, the ROM is immutable and you are modifying the codec to your liking until the string
representation looks the way you want it to.

## PROM

A PROM (Programmable ROM) is similar to an IROM except that its bytestring representation is
modifiable while its string representation is immutable.

## EROM

* IROM: To modify a character c into c' is to change a codec entry b <-> c into b <-> c'.
  The underlying ROM is immutable.
* PROM: To modify a byte b into b' is to change a codec entry b <-> c into b' <-> c.
  The decoded string is immutable.
* EROM: To modify a byte b into b' is to also modify the corresponding character c into c';
  To modify a byte c into c' is to also modify the corresponding byte b into b';
  where the codec contains entries b <-> c and b' <-> c'.
  The codec is immutable.

# Script dumping

Transforming a raw ROM into a readable string representation is similar to solving a jigsaw puzzle:
there is an initial phase where you piece together the edge pieces. Once finished, the second phase
-- where you piece together the internal pieces -- becomes considerably easier.

To dump the script contained in a ROM is to construct a Unicode string representation of the relevant
portions of the ROM.

1. Create a ROM instance from the path of the file
2. Find some text in the ROM
3. Create an IROM instance from the ROM
4. Enforce the bytes in the found range to map to the desired string
5. Study the resulting string representation visually and try to find more bytes that you can associate
   with characters
6. Repeat step 4-5 until you are happy with the string representation.
7. Save it to a file

## Example

1. Create a ROM instance from the path of the file.

```
>>> rom = ROM('persona1usa/TENSI.BIN', structure=SimpleTopology(2))
```

2. Search for some text you know is stored in the ROM somewhere.

```
>>> a, b = rom.search("How charming")
```

3. Create an IROM from the ROM.

```
>>> irom = IROM(rom)
```

4. Enforce the bytes in this range to map to the desired string.

```
>>> irom[a:b] = "How charming"
```

5. Study the resulting string representation visually and try to find more bytes that you can associate
   with characters.

```
>>> print(irom)
```

6. Repeat step 4-5 until you are happy with the string representation.
7. Save it to a file.
