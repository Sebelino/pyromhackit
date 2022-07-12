import math
from typing import List

import matplotlib.pyplot as plt

from pyromhackit.gslice.selection import Selection


def selection2bitarray(selection: Selection) -> List[float]:
    excluded_number = 0.0
    included_number = 1.0
    bit_array = []
    last_end = 0
    for a, b in selection.pairs():
        for _ in range(last_end, a):
            bit_array.append(excluded_number)
        for _ in range(a, b):
            bit_array.append(included_number)
        last_end = b
    for _ in range(last_end, selection.universe.stop):
        bit_array.append(excluded_number)
    return bit_array


def bitarray2bitmatrix(bit_array: List[float]) -> List[List[float]]:
    absent_number = 0.5
    width = 2 ** math.ceil(math.log2(math.sqrt(len(bit_array))))
    bit_matrix = []
    for i, n in enumerate(bit_array):
        if i % width == 0:
            bit_matrix.append([])
        bit_matrix[-1].append(n)
    if len(bit_matrix[-1]) != bit_matrix[0]:
        residue = [absent_number for _ in range(len(bit_matrix[-1]), len(bit_matrix[0]))]
        bit_matrix[-1].extend(residue)
    return bit_matrix


def plot_selection(selection: Selection):
    bit_array = selection2bitarray(selection)
    bit_matrix = bitarray2bitmatrix(bit_array)
    plt.imshow(bit_matrix)
    plt.show()
