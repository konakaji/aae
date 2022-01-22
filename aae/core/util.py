import math, numpy as np


def print_state_tex(values, n_qubit):
    result = ""
    for i, v in enumerate(values):
        bit_array = num_to_bitarray(i, n_qubit)
        str = to_bitstring(bit_array)
        if i > 0 and v >= 0:
            result = result + "+"
        elif v < 0:
            result = result + "-"
        result = result + "{:.2f}|{}>".format(abs(v), str)
    return result


def num_to_bitarray(num, N):
    result = []
    value = num
    for n in range(N):
        div = pow(2, N - 1 - n)
        result.append(math.floor(value / div))
        value = value - div * math.floor(value / div)
    return result


def to_bitstring(bitarray):
    result = ""
    for b in bitarray:
        result = result + str(b)
    return result
