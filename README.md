# Thousand Curses
ncurses-based editor geared towards editing ROM (Read-only memory) files containing text stored in arbitrarily complex encodings.

The editor consists of two windows, one showing the ROM in hexadecimal notation and one showing the ROM in whatever decoding you choose to specify.

## Usage
```
$ python thousand_curses.py ROM CODEC [-h]
```
Press CTRL+G to exit.

## Examples
```
$ python thousand_curses.py loremipsum.rom MonospaceASCIISeq
```

```
$ python thousand_curses.py mt2-excerpt.sfc Mt2GarbagePair
```


