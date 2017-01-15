Python ROM Hacking Toolkit (pyromhackit)
=========================================
This is a little Python utility providing my tools for doing ROM hacks, primarily geared towards
script replacement. This is still largely a work in progress.

[![Build Status](https://travis-ci.org/Sebelino/pyromhackit.svg?branch=master)](https://travis-ci.org/Sebelino/pyromhackit)
[![Code Health](https://landscape.io/github/Sebelino/pyromhackit/master/landscape.svg?style=flat)](https://landscape.io/github/Sebelino/pyromhackit/master)

# Install
TODO

## Dependencies
* Python 3

Install the dependencies like so:
```bash
$ pip install -r requirements.txt
```

# Usage
**reader.py** provides a kind of pipeline interface for processing a ROM. More information to come...
```bash
$ ./reader.py -h
usage: reader.py [-h]
                 [--transliteration TRANSLITERATION [TRANSLITERATION ...]]
                 [--width WIDTH] [--outfile OUTFILE]
                 infile {bin,hex}
                 [{odd,hex,text,map,replace,pack,join,table,label} [{odd,hex,text,map,replace,pack,join,table,label} ...]]

Read a ROM and process it.

positional arguments:
  infile                Path to the file to be read.
  {bin,hex}             Encoding of the read file.
  {odd,hex,text,map,replace,pack,join,table,label}
                        Apply processing rules to the out-encoded stream.

optional arguments:
  -h, --help            show this help message and exit
  --transliteration TRANSLITERATION [TRANSLITERATION ...], -t TRANSLITERATION [TRANSLITERATION ...]
                        YAML file mapping a set of symbols to another set of
                        symbols.
  --width WIDTH, -w WIDTH
                        Number of columns in the output.
  --outfile OUTFILE, -o OUTFILE
                        Output to file instead of to console.
```

## Examples
```
$ ./reader.py majin-tensei-ii/mt2.sfc bin map text -t majin-tensei-ii/hexmap.yaml -o out.txt
```

## Testing
```bash
$ nosetests
```

Features
========
Functional requirements:
* Palette formatter
* ROM file reader module providing a pipeline interface to the ROM file.

Quality requirements:
* Platform independence
* Free software license

Status
======
Romhacks I am considering or lightly working on at the moment:
* Majin Tensei II translation. Aeon Genesis has called dibs on this one, but progress on the prequel
has been stuck at 40 % since forever.
* Actraiser 2 retranslation/decensoring. Decent warmup project.
* Devil Summoner translation. A script exists but development with hacking the ISO appears to be
stuck in limbo.
* Persona (PSP) soundtrack patch. There exists one, but it is far from perfect.

# License
The software is licensed under GPLv3. See LICENSE.md for details.
