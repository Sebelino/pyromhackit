#!/usr/bin/env python

""" Provides algorithms for identifying English text in files that may contain English text mixed with other data. """

from io import TextIOBase
from langid.langid import LanguageIdentifier, model

from selection import Selection

identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

path = "/home/sebelino/lib/python3/pyromhackit/pyromhackit/roms/persona1usa/output/basket.bin.view.txt"

with open(path, 'r') as f:
    content = f.read()


def identify_language(content, segment_size: int):
    segmented_content = [(i, content[i:i + segment_size]) for i in range(0, len(content), segment_size)]
    verdict = [(offset, string, identifier.classify(string)) for offset, string in segmented_content]
    return verdict


def duplicate(n, lst):
    return [x for x in lst for _ in range(n)]


def annotate(classifications):
    return ''.join(' ' if c[0] == 'en' else 'x' for c in classifications)

def judge(content):
    verdict1 = identify_language(content, 200)
    verdict2 = identify_language(content, 100)
    verdict3 = identify_language(content, 50)
    verdict4 = identify_language(content, 25)

    verdict = [
        (''.join(annotate([c1, c2, c3, c4])), o4, s4) for (_, _, c1), (_, _, c2), (_, _, c3), (o4, s4, c4) in
        zip(duplicate(8, verdict1), duplicate(4, verdict2), duplicate(2, verdict3), verdict4)
    ]
    return verdict


def separate(verdict) -> Selection:
    total_length = verdict[-1][1] + len(verdict[-1][2])
    garbage_selection = Selection(universe=slice(0, total_length))
    for label, offset, substring in verdict:
        not_english = label.strip() == label
        if not_english:
            garbage_selection.coverup(offset, offset + len(substring))
    tolerance = 25
    garbage_selection.reveal_partially(None, None, tolerance)
    return garbage_selection

judgement = judge(content)
separation = separate(judgement)


def stream2english(stream: TextIOBase):
    """ @stream A stream of arbitrary Unicode characters. :return an iterator for substrings of @stream such that every
    every substring consists only of English characters and such that all substrings together constitute all of the
    English text in the stream. """
