# Thousand Curses
Python- and ncurses-based editor geared towards editing ROM (Read-only memory) files containing text stored in arbitrarily complex formats.

The editor consists of two windows side-by-side: one displaying the ROM in hexadecimal decoding and one displaying the ROM in whatever decoding you choose to specify. The available codecs can be found in `codec.py`.

## Usage
```
$ python thousand_curses.py ROM CODEC [-h]
```
Press CTRL+G to exit.

## Examples
```
$ python thousand_curses.py loremipsum.rom MonospaceASCIISeq
```
![](https://cloud.githubusercontent.com/assets/837775/21470130/a809e35a-ca7b-11e6-8744-519370aed4b6.png)

```
$ python thousand_curses.py mt2-excerpt.sfc Mt2GarbageTextPair
```
![](https://cloud.githubusercontent.com/assets/837775/21470137/d662dbe4-ca7b-11e6-8ff0-78e853271ac0.png)

