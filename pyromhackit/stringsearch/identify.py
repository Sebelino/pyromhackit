#!/usr/bin/env python

""" Provides algorithms for identifying English text in files that may contain English text mixed with other data. """
import os
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from io import TextIOBase

import sys
from termcolor import colored

from pyromhackit.selection import Selection
from pyromhackit.util import findall

package_dir = os.path.dirname(os.path.abspath(__file__))


class TextIdentifier(metaclass=ABCMeta):
    """ Abstraction for a way of identifying text in a sequence of arbitrary Unicode characters. """

    @abstractmethod
    def stream2selection(self, stream: TextIOBase) -> Selection:
        """ :return A selection of the stream of Unicode characters @stream such that it selects the desired text.
        Must not be called before the instance has been initialized. """
        raise NotImplementedError

    @abstractmethod
    def str2selection(self, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects the desired text.
        Must not be called before the instance has been initialized. """
        raise NotImplementedError


class DictionaryBasedTextIdentifier(TextIdentifier, metaclass=ABCMeta):
    """ ITextIdentifier based on finding text using a set of strings ("words"). """

    @abstractmethod
    def wordlist(self) -> frozenset:
        """ :return The set of words used for lookup. """
        raise NotImplementedError

    @abstractmethod
    def str2wordlistselection(self, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects all words found in @string. """
        raise NotImplementedError

    @abstractmethod
    def caseinsensitivestr2wordlistselection(self, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects all words found in @string with no
        regard to letter case. """
        raise NotImplementedError


class EnglishDictionaryBasedIdentifier(DictionaryBasedTextIdentifier):
    def __init__(self, tolerated_char_count=0):
        """ @tolerated_char_count is the number of characters surrounding the found words that will be included in the
        identified text. """
        with open(os.path.join(package_dir, "resources/cracklib-small-subset.txt")) as f:
            self._wordlist = f.read()
        self._wordlist = self._wordlist.strip()
        self._wordlist = self._wordlist.split()
        self._wordlist = frozenset(self._wordlist)
        self._tolerated_char_count = tolerated_char_count

    def wordlist(self) -> frozenset:
        return self._wordlist

    def str2wordlistselection(self, string: str) -> Selection:
        textselection = Selection(universe=slice(0, len(string)))
        textselection.exclude(None, None)
        for word in iter(self.wordlist()):
            for startindex in findall(word, string):
                textselection.include(startindex, startindex + len(word))
        return textselection

    def caseinsensitivestr2wordlistselection(self, string: str) -> Selection:
        return self.str2wordlistselection(string.lower())

    def stream2selection(self, stream: TextIOBase) -> Selection:
        return self.str2selection(stream.read())

    def str2selection(self, string: str) -> Selection:
        dictselection = self.caseinsensitivestr2wordlistselection(string)
        textselection = deepcopy(dictselection)
        textselection.include_expand(None, None, self._tolerated_char_count)
        return textselection


if __name__ == '__main__':
    """ Reads Unicode data from stdin and finds English text in it. """
    identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=10)
    content = open(sys.argv[1]).read() if len(sys.argv) == 2 else sys.stdin.read()
    dictselection = identifier.caseinsensitivestr2wordlistselection(content)
    textselection = identifier.str2selection(content)
    print("Dictionary selection: {}".format(list(dictselection)))
    print("Text selection: {}".format(list(textselection)))
    print()
    for a, b in textselection:
        print("{:3}...{:3}: \"".format(a, b), end="")
        subselection = dictselection.subslice(a, b)
        seekindex = a
        for c, d in subselection:
            gap = content[seekindex:c]
            body = content[c:d]
            seekindex = d
            print(repr(gap)[1:-1] + colored(repr(body)[1:-1], "blue"), end="")
        endgap = content[seekindex:b]
        print(repr(endgap)[1:-1] + "\"")
