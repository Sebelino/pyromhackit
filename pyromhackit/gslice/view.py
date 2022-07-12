import termcolor

from .selection import Selection


def highlight_each_selection(string: str, selection: Selection, context_char_length: int):
    for a, b in selection.pairs():
        word = string[a + context_char_length:b - context_char_length]
        pre = string[a:a + context_char_length]
        suf = string[b - context_char_length:b]
        print(pre + termcolor.colored(word.upper(), 'red') + suf)
