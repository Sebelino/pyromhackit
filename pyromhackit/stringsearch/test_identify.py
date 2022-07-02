#!/usr/bin/env python

import pytest

from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier, DictionaryBasedTextIdentifier
from pyromhackit.gslice.selection import Selection


class TestEnglishDictionaryBasedIdentifier(object):
    two_embedded_strings = (
        "ÿþýüûúùø÷ö"  # 10
        + "hello"  # 15
        + "ðïîíìëêéèçæåäãâáàßÞÝÜÛÚÙØ"  # 40
        + "The quick brown fox jumps over the lazy dog"  # 83
        + "¬«ª©¨§¦¥¤£¢¡\x7f~}|{zyxwvutsrqponmlkjihgfedcba`_^]\\["
        + "ZYXWVUTSRQPONMLKJIHGFEDCBA@?>=<;:9876543210/.-,+*)(\'&%$#\"!")

    @pytest.fixture
    def identifier(self) -> DictionaryBasedTextIdentifier:
        return EnglishDictionaryBasedIdentifier(tolerated_char_count=1)

    @pytest.fixture(params=[
        ("hello", Selection(universe=slice(0, 5), revealed=[slice(0, 5)])),
        ("hello there", Selection(universe=slice(0, 11), revealed=[slice(0, 5), slice(6, 11)])),
        (two_embedded_strings, Selection(universe=slice(0, len(two_embedded_strings)), revealed=[
            (10, 15),  # hello
            (40, 43),  # The
            (44, 49),  # quick
            (50, 55),  # brown
            (56, 59),  # fox
            (60, 65),  # jumps
            (66, 70),  # over
            (71, 74),  # the
            (75, 79),  # lazy
            (80, 83),  # dog
        ])),
    ])
    def input_output(self, request):
        return request.param

    def test_caseinsensitivestr2dictionaryselection(self, identifier: DictionaryBasedTextIdentifier, input_output):
        basestr, expected = input_output
        returned = identifier.caseinsensitivestr2wordlistselection(basestr)
        assert expected == returned

    @pytest.fixture(params=[
        ("hello", "hello"),
        ("hello there", "hello there"),
        ("hello", two_embedded_strings),
        ("The quick brown fox jumps over the lazy dog", two_embedded_strings),
    ])
    def substring_basestring(self, request):
        return request.param

    def test_str2selection(self, identifier: DictionaryBasedTextIdentifier, substring_basestring):
        substring, basestring = substring_basestring
        textselection = identifier.str2selection(basestring)
        selected_text = textselection.select(basestring)
        assert substring in selected_text
