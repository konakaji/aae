from numpy import array, copy


def walsh_hadamard_transform(a: array):
    h = 1
    complexity = 0
    a = copy(a)
    while h < len(a):
        for i in range(0, len(a), h * 2):
            for j in range(i, i + h):
                x = a[j]
                y = a[j + h]
                a[j] = x + y
                a[j + h] = x - y
                complexity = complexity + 1
        h *= 2
    return a
