import difflib
from collections import namedtuple
from copy import deepcopy

from math import ceil

import re
from typing import Optional

import mmap
from prettytable import PrettyTable

from pyromhackit.gmmap import StringMmap, SourcedGMmap, SelectiveGMmap
from pyromhackit.selection import Selection
from pyromhackit.thousandcurses.codec import Tree
from pyromhackit.tree import SimpleTopology
from pyromhackit.rom import ROM


class IROMMmap(SourcedGMmap, StringMmap):
    # TODO make these IROM Gmmaps not depend on ROM, then move to gmmap.py. Should be decoupled from this library
    """ A StringMmap where the source is extracted from a ROM and a codec mapping ROM atoms to strings. """

    def __init__(self, rom: ROM, codec):
        source = (codec[atom] for atom in rom)
        self._content = self._source2mmap(source)
        self._length = rom.atomcount()
        self._path = None

    @property
    def _content(self) -> mmap.mmap:
        return self._m_content

    @property
    def _path(self) -> Optional[str]:
        return self._m_path

    @property
    def _length(self) -> int:
        return self._m_length

    @_content.setter
    def _content(self, value):
        self._m_content = value

    @_length.setter
    def _length(self, value):
        self._m_length = value

    @_path.setter
    def _path(self, value):
        self._m_path = value


class SelectiveIROMMmap(SelectiveGMmap, IROMMmap):

    def __init__(self, rom: ROM, codec):  # TODO reduce coupling, Hacker mediator
        super(SelectiveIROMMmap, self).__init__(rom, codec)
        self._selection = Selection(universe=slice(0, self._length))

    @property
    def selection(self) -> Selection:
        return self._selection

    def _nonvirtualint2physical(self, location: int):
        return slice(4 * location, 4 * (location + 1))

    def _nonvirtualselection2physical(self, location: Selection):
        return location * 4


class IROM(object):
    """ Isomorphism of a ROM. Basically a Unicode string with a structure defined on it. """

    def __init__(self, rom: 'ROM', codec):
        """ Constructs an IROM object from a ROM and a codec transliterating every ROM atom into an IROM atom. """
        self.structure = SimpleTopology(1)  # This will do for now
        self.text_encoding = 'utf-32'
        self.memory = SelectiveIROMMmap(rom, codec)

    def selection(self):
        return deepcopy(self.memory.selection)

    def coverup(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.coverup_virtual(from_index, to_index)
        else:
            self.memory.coverup(from_index, to_index)

    def reveal(self, from_index, to_index, virtual=True):  # Mutability
        if virtual:
            self.memory.uncover_virtual(from_index, to_index)
        else:
            self.memory.uncover(from_index, to_index)

    def tree(self):
        t = self.structure.structure(self[:])
        return Tree(t)

    def traverse_preorder(self):
        for idx, atomidx, idxpath, content in self.structure.traverse_preorder(self):
            byteindex = self.index2slice(idx).start
            yield idx, atomidx, idxpath, byteindex, str(content)

    def index2slice(self, idx):  # TODO Abstraction leak -- remove (?)
        """ Returns a slice indicating where the bytes necessary to encode the @idx'th character are stored. """
        if idx >= len(self):
            raise IndexError("IROM index out of range: {}".format(idx))
        modidx = idx % len(self)
        if self.text_encoding == 'utf-32':
            return slice(4 + 4 * modidx, 4 + 4 * (modidx + 1))
        raise NotImplementedError()

    def __getitem__(self, val):
        return self.memory[val]

    def getatom(self, atomindex):  # TODO duplicate of getitem at this point
        """ :return The @atomindex'th atom in this memory. """
        return str(self.structure.getleaf(atomindex, self))

    def atomindex2entry(self, atomindex: int):
        Atom = namedtuple("Atom", "index atomindex indexpath byteindex content")
        indexpath = self.structure.leafindex2indexpath(atomindex)
        index = self.structure.indexpath2index(indexpath)
        content = self.getatom(atomindex)
        byteindex = self.index2slice(index).start
        return Atom(index, atomindex, indexpath, byteindex, content)

    def __len__(self):
        """ :return The number of characters in this IROM. """
        return len(self.memory)

    def atomcount(self):  # TODO __len__ duplicate (?)
        return len(self.memory)

    def __str__(self):
        if len(self.memory) > 10 ** 7:  # Assumes that IROM atoms are on average short
            raise MemoryError("IROM too large to convert to string")
        return self[:]

    def find(self, *args):
        return str(self).find(*args)

    def finditer(self, pattern):
        """ Returns an ordered list of matches with span=(a, b) such that self[a:b] matches @pattern. """
        return re.finditer(pattern, str(self))

    def first_match(self, pattern):
        """ Return the first match for the given pattern. """
        return next(self.finditer(pattern))

    def first_group(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).group(1)

    def first_group_index(self, pattern):
        """ Return the start index of the first group of the first match for the given pattern. """
        return self.first_match(pattern).start(1)

    def grep(self, pattern, context=50, labels=True):
        for m in self.finditer(pattern):
            s = m.string[m.start() - context:m.end() + context]
            label = ""
            if labels:
                label = "{}: ".format(hex(m.start()))
            print("{}{}".format(label, s))

    def table(self, cols=16, label=True, border=True, padding=1):
        """ Display the stream of characters in a table. """
        fields = [''] + [hex(i)[2:] for i in range(cols)]
        table = PrettyTable(field_names=fields, header=True, border=border, padding_width=padding)
        content = str(self)
        labelwidth = len(str(len(content)))
        for i in range(0, len(content), cols):
            segment = content[i:i + cols]
            segment = segment + " " * max(0, cols - len(segment))
            segment = list(segment)
            if label:
                fmtstr = "{:>" + str(labelwidth) + "}: "
                segment = [fmtstr.format(hex(i)[2:])] + segment
            table.add_row(segment)
        return table

    def grep_table(self, searchstring, context=3, cols=16, label=True, border=True, padding=1):
        s = str(self)
        idx = s.index(searchstring)
        tbl = self.table(cols, label, border, padding)
        arow = int(idx / cols) - context
        brow = int(idx / cols) + ceil(len(searchstring) / cols) + context
        return tbl[arow:brow]

    def __setitem__(self, key, value):
        raise NotImplementedError()  # TODO

    def dump(self, path):
        """ Writes the content of this IROM to a file with path @path. """
        with open(path, 'w') as f:
            f.write(self.memory[:])

    def diff_chunks_from_copy(self, edited_content):
        """ File @path contains a string identical to this IROM except that zero or more substrings have been removed.
        :return A list of diff chunks describing what parts of the lines have changed.
        """
        d = difflib.Differ()
        original_content = self[:]
        diff = d.compare(original_content.split('\n'), edited_content.split('\n'))
        # Match added lines with removed lines
        lines = []
        original_offset = 0
        edited_offset = 0
        for diffline in diff:
            prefix = diffline[:2]
            line = diffline[2:]
            delta = len(line) + 1  # Line length + \n
            if prefix == '- ':
                lines.append((prefix, original_offset, line))
                original_offset += delta
            elif prefix == '+ ':
                lines.append((prefix, edited_offset, line))
                edited_offset += delta
            elif prefix == '  ':
                lines.append((prefix, (original_offset, edited_offset), line))
                original_offset += delta
                edited_offset += delta
        adjacentlines = list(zip([(None, None, None)] + lines, lines + [(None, None, None)]))
        start_indices = [i for i, ((p1, _, _), (p2, _, _)) in enumerate(adjacentlines)
                         if p1 in {None, '  '} and p2 in {'- ', '+ '}]
        stop_indices = [i for i, ((p1, _, _), (p2, _, _)) in enumerate(adjacentlines)
                        if p1 in {'- ', '+ '} and p2 in {None, '  '}]
        chunks = [lines[slice(a, b)] for a, b in zip(start_indices, stop_indices)]
        # Strip away empty added lines
        chunks = [[(a, b, c) for a, b, c in chunk if not (a == '+ ' and len(c) == 0)] for chunk in chunks]
        # INV: Every chunk is a list of n >= 1 triplets with '- ' prefix followed by m <= n triplets with prefix '+ '
        return chunks

    @staticmethod
    def _string_selection_of(selstring, string):
        """ :return True iff string1 is string2 but with zero or more characters removed. """
        seqm = difflib.SequenceMatcher(None, string, selstring)
        for opcode, i1, i2, j1, j2 in seqm.get_opcodes():
            if opcode not in {'delete', 'equal'}:
                return False
        return True

    @classmethod
    def _organize_chunk(cls, chunk):
        """ Takes @chunk -- a collection of lines that are removed/added -- as input. @return A collection of removed
        lines paired with a collection consisting of pairs (R, A) where R is the removed line and A is the added line
        that corresponds to it. """
        altered_difflines = [diffline for diffline in chunk if diffline[0] == '- ']
        added_difflines = [diffline for diffline in chunk if diffline[0] == '+ ']
        removed_difflines = set(altered_difflines)
        matched_diffline_pairs = []
        for added_diffline in added_difflines:
            found_match = False
            _, _, added_line = added_diffline
            for altered_diffline in altered_difflines:
                _, _, altered_line = altered_diffline
                if cls._string_selection_of(added_line, altered_line):
                    assert not found_match, "Found two removed lines that may both correspond to the same added line."
                    found_match = True
                    matched_diffline_pairs.append((altered_diffline, added_diffline))
                    removed_difflines.remove(altered_diffline)
            assert found_match, "Found no removed line that corresponds to the added line."
        return removed_difflines, matched_diffline_pairs

    @classmethod
    def removals_from_copy(cls, original_content, edited_content) -> Selection:
        """ :return A collection of intervals that specify the sections of the edited IROM copy pointed out by @path
        that have been removed. """
        chunks = cls.diff_chunks_from_copy(original_content, edited_content)
        removals = Selection(universe=slice(0, len(original_content)), revealed=[])
        for chunk in chunks:
            removed_lines, matched_line_pairs = cls._organize_chunk(chunk)
            for prefix, offset, line in removed_lines:
                removals.reveal(offset, offset + len(line) + 1)
            for rline, aline in matched_line_pairs:
                _, offset1, string1 = rline
                _, offset2, string2 = aline
                seqm = difflib.SequenceMatcher(None, string1, string2)
                for opcode, i1, i2, _, _ in seqm.get_opcodes():
                    if opcode == 'delete':
                        removals.reveal(offset1 + i1, offset1 + i2)
        return removals

    def load_selection_from_copy(self, path):
        """ File @path contains a string identical to this IROM except that zero or more substrings have been removed.
        The selection of this IROM is adjusted so that the substrings not present in @path become hidden.
        """
        with open(path, 'r') as f:
            edited_content = f.read()
        removed_count = 0
        removals = self.removals_from_copy(str(self), edited_content)
        for a, b in removals:
            self.coverup(a - removed_count, b - removed_count, virtual=True)
            removed_count += b - a
