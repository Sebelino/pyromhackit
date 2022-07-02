#!/usr/bin/env python

from pyromhackit.stringsearch.identify import EnglishDictionaryBasedIdentifier


class TestEnglishDictionaryBasedIdentifier(object):
    def setup(self):
        self.identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=0)
        # self.corpus = lorem.ipsum()[:1000]
        self.corpus = ("hello " * 1000)[:1000]

    def test_str2selection_2pow0(self, benchmark):
        corpus = self.corpus * 2 ** 0
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow1(self, benchmark):
        corpus = self.corpus * 2 ** 1
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow2(self, benchmark):
        corpus = self.corpus * 2 ** 2
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow3(self, benchmark):
        corpus = self.corpus * 2 ** 3
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_2pow4(self, benchmark):
        corpus = self.corpus * 2 ** 4
        benchmark(self.identifier.str2selection, corpus)


class TestEnglishDictionaryBasedIdentifierTolerated(object):
    def setup(self):
        self.identifier = EnglishDictionaryBasedIdentifier(tolerated_char_count=5)
        # self.corpus = lorem.ipsum()[:1000]
        self.corpus = ("hello " * 1000)[:1000]

    def test_str2selection_tolerated_2pow0(self, benchmark):
        corpus = self.corpus * 2 ** 0
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_tolerated_2pow1(self, benchmark):
        corpus = self.corpus * 2 ** 1
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_tolerated_2pow2(self, benchmark):
        corpus = self.corpus * 2 ** 2
        benchmark(self.identifier.str2selection, corpus)

    def test_str2selection_tolerated_2pow3(self, benchmark):
        corpus = self.corpus * 2 ** 3
        benchmark(self.identifier.str2selection, corpus)
