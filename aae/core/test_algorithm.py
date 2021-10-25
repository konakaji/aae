from unittest import TestCase
import numpy as np
from math import sqrt
from svd.core.algorithm import walsh_hadamard_transform


class Test(TestCase):
    def test_walsh_hadamard_transform(self):
        a_ = [np.array([0, 1, 0, 0]),
              np.array([0, 1, 0, 0]),
              np.array([0, -1/sqrt(2), 1/sqrt(2), 0]),
              np.array([0.5, 0.5, 0.5, 0.5]),
              np.array([sqrt(0.05), -sqrt(0.49), sqrt(0.15), sqrt(0.31)])
              ]
        for a in a_:
            h = np.array([[1 / 2, 1 / 2, 1 / 2, 1 / 2],
                          [1 / 2, -1 / 2, 1 / 2, -1 / 2],
                          [1 / 2, 1 / 2, -1 / 2, -1 / 2],
                          [1 / 2, -1 / 2, -1 / 2, 1 / 2]])
            b = h.dot(a)
            a, c = walsh_hadamard_transform(a)
            np.testing.assert_array_almost_equal(a * 0.5, b)
            print(c)
