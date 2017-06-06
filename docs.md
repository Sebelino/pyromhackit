# ROM
A ROM (Read-only memory) -- in the context of this ROM-hacking library -- is an object holding a
read-only sequence of bytes. This source of this sequence may be a file, or simply a raw bytestring.
Since byte sequences loaded from a file tend to be large, and you may only be interested in a small
portion of the file, you have the option of ignoring arbitary sections of the file.
In addition, you may define a hierarchical structure on the ROM. A common structure is the two-byte
structure, where the ROM is divided into a sequence of items where each item is a bytestring of
length 2. We may call each leaf in such a bytestring tree a ROM atom.

# IROMs
An IROM (Isomorphism of a ROM) is an alternative way to represent a ROM, intended to be more
readable. An IROM instance is created from a ROM instance and provides a way to construct a semantics
for the ROM's content.
An IROM instance consists of a ROM, paired with a tree of strings such that there is
a codec -- a one-to-one correspondence -- between each ROM atom and each string leaf.
In an IROM, the ROM is immutable and you are modifying the codec to your liking until the string
representation looks the way you want it to.

# PROM
A PROM (Programmable ROM) is similar to an IROM except that its bytestring representation is
modifiable while its string representation is immutable.


# ROM-hacking workflow
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
6. Repeat step 4-5 until you are happy with the codec.
