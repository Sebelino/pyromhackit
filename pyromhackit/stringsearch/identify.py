#!/usr/bin/env python

""" Provides algorithms for identifying English text in files that may contain English text mixed with other data. """
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from io import TextIOBase

import sys
from langid.langid import LanguageIdentifier, model
from termcolor import colored

from pyromhackit.selection import Selection
from pyromhackit.util import findall


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
    def dictionary(self) -> frozenset:
        """ :return The set of words used for lookup. """
        raise NotImplementedError

    @abstractmethod
    def str2dictionaryselection(self, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects all words found in @string. """
        raise NotImplementedError

    @abstractmethod
    def caseinsensitivestr2dictionaryselection(self, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects all words found in @string. """
        raise NotImplementedError


class EnglishDictionaryBasedIdentifier(DictionaryBasedTextIdentifier):
    def __init__(self, tolerated_char_count=0):
        """ @tolerated_char_count is the number of characters surrounding the found words that will be included in the
        identified text. """
        with open("/home/sebelino/lib/python3/pyromhackit/pyromhackit/cracklib-small-subset.txt") as f:
            self._dictionary = f.read()
        self._dictionary = self._dictionary.strip()
        self._dictionary = self._dictionary.split()
        self._dictionary = frozenset(self._dictionary)
        self._tolerated_char_count = tolerated_char_count

    def dictionary(self) -> frozenset:
        return self._dictionary

    def str2dictionaryselection(self, string: str) -> Selection:
        textselection = Selection(universe=slice(0, len(string)))
        textselection.coverup(None, None)
        for word in iter(self.dictionary()):
            for startindex in findall(word, string):
                textselection.reveal(startindex, startindex + len(word))
        return textselection

    def caseinsensitivestr2dictionaryselection(self, string: str) -> Selection:
        return self.str2dictionaryselection(string.lower())

    def stream2selection(self, stream: TextIOBase) -> Selection:
        return self.str2selection(stream.read())

    def str2selection(self, string: str) -> Selection:
        dictselection = self.caseinsensitivestr2dictionaryselection(string)
        textselection = deepcopy(dictselection)
        textselection.reveal_expand(None, None, self._tolerated_char_count)
        return textselection


class EnglishLangidBasedIdentifier(TextIdentifier):
    """ Identifies English text by using the langid library. """

    _identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

    def stream2selection(self, stream: TextIOBase) -> Selection:
        return self.str2selection(stream.read())

    def str2selection(self, string: str) -> Selection:
        verdict = self._judge(string)
        selection = self._separate(verdict)
        tolerated_selection = self._tolerate(selection)
        return tolerated_selection

    @classmethod
    def stream2text(cls, stream: TextIOBase):
        """ @stream A stream of arbitrary Unicode characters. :return an iterator for substrings of @stream such that every
        every substring consists only of English characters and such that all substrings together constitute all of the
        English text in the stream. """
        sel = cls.stream2selection(stream)
        return sel.select(stream)

    @classmethod
    def _identify_language(cls, content, segment_size: int):
        segmented_content = [(i, content[i:i + segment_size]) for i in range(0, len(content), segment_size)]
        verdict = [(offset, string, cls._identifier.classify(string)) for offset, string in segmented_content]
        return verdict

    @staticmethod
    def _duplicate(n, lst):
        return [x for x in lst for _ in range(n)]

    @staticmethod
    def _annotate(classifications):
        return ''.join(' ' if c[0] == 'en' else 'x' for c in classifications)

    @classmethod
    def _judge(cls, content):
        verdict1 = cls._identify_language(content, 200)
        verdict2 = cls._identify_language(content, 100)
        verdict3 = cls._identify_language(content, 50)
        verdict4 = cls._identify_language(content, 25)

        verdict = [
            (''.join(cls._annotate([c1, c2, c3, c4])), o4, s4) for (_, _, c1), (_, _, c2), (_, _, c3), (o4, s4, c4) in
            zip(cls._duplicate(8, verdict1), cls._duplicate(4, verdict2), cls._duplicate(2, verdict3), verdict4)
        ]
        return verdict

    @staticmethod
    def _separate(verdict) -> Selection:
        total_length = verdict[-1][1] + len(verdict[-1][2])
        garbage_selection = Selection(universe=slice(0, total_length))
        for label, offset, substring in verdict:
            not_english = label.strip() == label
            if not_english:
                garbage_selection.coverup(offset, offset + len(substring))
        return garbage_selection

    @staticmethod
    def _tolerate(garbage_selection: Selection):
        tolerance = 25
        sel = deepcopy(garbage_selection)
        sel.reveal_expand(None, None, tolerance)
        return sel


if __name__ == '__main__':
    """ Reads Unicode data from stdin and finds English text in it. """
    identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=10)
    content = sys.stdin.read()
    dictselection = identifier.caseinsensitivestr2dictionaryselection(content)
    textselection = identifier.str2selection(content)
    print("Dictionary selection: {}".format(list(dictselection)))
    print("Text selection: {}".format(list(textselection)))
    print()
    for a, b in textselection:
        print("{:3}...{:3}: \"".format(a, b), end="")
        subselection = dictselection.subselection(a, b)
        seekindex = a
        for c, d in subselection:
            gap = content[seekindex:c]
            body = content[c:d]
            seekindex = d
            print(repr(gap)[1:-1] + colored(repr(body)[1:-1], "blue"), end="")
        endgap = content[seekindex:b]
        print(repr(endgap)[1:-1]+"\"")
