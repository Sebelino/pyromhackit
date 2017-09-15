#!/usr/bin/env python

""" Provides algorithms for identifying English text in files that may contain English text mixed with other data. """
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from io import TextIOBase
from langid.langid import LanguageIdentifier, model

from pyromhackit.selection import Selection


class ITextIdentifier(metaclass=ABCMeta):
    """ Abstraction for a way of identifying text in a sequence of arbitrary Unicode characters. """

    @classmethod
    @abstractmethod
    def stream2selection(cls, stream: TextIOBase) -> Selection:
        """ :return A selection of the stream of Unicode characters @stream such that it selects the desired text. """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def str2selection(cls, string: str) -> Selection:
        """ :return A selection of the Unicode string @string such that it selects the desired text. """
        raise NotImplementedError


class EnglishIdentifierLangid(ITextIdentifier):
    """ Identifies English text by using the langid library. """

    _identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

    @classmethod
    def stream2selection(cls, stream: TextIOBase) -> Selection:
        return cls.str2selection(stream.read())

    @classmethod
    def str2selection(cls, string: str) -> Selection:
        verdict = cls._judge(string)
        selection = cls._separate(verdict)
        tolerated_selection = cls._tolerate(selection)
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
