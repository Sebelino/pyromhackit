import unicodedata

import termcolor

from .selection import Selection


def substitute_nonprintable(string: str, substitution_char: str):
    printable_categories = {'Lu', 'Ll', 'Zs', 'Nd'}
    return "".join(c if unicodedata.category(c) in printable_categories else substitution_char for c in string)


def highlight_each_selection(string: str, selection: Selection, context_char_length: int):
    for a, b in selection.pairs():
        word = string[a:b]
        pre = substitute_nonprintable(string[a - context_char_length:a], ".")
        suf = substitute_nonprintable(string[b:b + context_char_length], ".")
        print(pre + termcolor.colored(word.upper(), 'red') + suf)
