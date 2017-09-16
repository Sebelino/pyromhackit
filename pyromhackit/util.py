#!/usr/bin/env python

""" General-purpose functions that do not fit anywhere else """
import itertools


def findall(substr: str, string: str):
    """ :return A list sorted in ascending order containing indices indicating where @substr is found in @string. """
    indices = []
    startindex = 0
    while True:
        startindex = string.find(substr, startindex)
        if startindex < 0:
            break
        indices.append(startindex)
        startindex += len(substr)
    return indices


def ascii_printables():
    """ :return A Unicode string consisting of every printable symbol between 0 and 255. """
    return ''.join(chr(i) for i in itertools.chain(range(33, 128), range(161, 256)))


def embed_strings(basestring: str, embeddables: dict):
    """ :return The string constructed by, for every entry (i, s) in @embeddables, embedding string s into @basestring
    at index i. """
    substrings = []
    seekidx = 0
    for embedidx, embedstr in iter(sorted(embeddables.items())):
        substrings.append(basestring[seekidx: embedidx])
        seekidx = embedidx
        if embedidx + len(embedstr) <= len(basestring):
            substrings.append(embedstr)
            seekidx += len(embedstr)
        elif embedidx < len(basestring) < embedidx + len(embedstr):
            substrings.append(embedstr[:len(basestring) - embedidx])
            seekidx += len(basestring) - embedidx
        else:
            seekidx = len(basestring)
            break
    substrings.append(basestring[seekidx:len(basestring)])
    return ''.join(substrings)
