#!/usr/bin/env python

""" Provides algorithms for identifying English text in files that may contain English text mixed with other data. """

from io import TextIOBase
from langid.langid import LanguageIdentifier, model


identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

path = "/home/sebelino/lib/python3/pyromhackit/pyromhackit/roms/persona1usa/output/basket.bin.view.txt"

with open(path, 'r') as f:
    content = f.read()

def stream2english(stream: TextIOBase):
    """ @stream A stream of arbitrary Unicode characters. :return an iterator for substrings of @stream such that every
    every substring consists only of English characters and such that all substrings together constitute all of the
    English text in the stream. """
