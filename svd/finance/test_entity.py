from unittest import TestCase
from svd.finance.entity import StateCoefficient
from svd.core.algorithm import walsh_hadamard_transform
from math import sqrt
import numpy as np

#
# class TestStateCoefficient(TestCase):
#     def test_to_hadamard_probability(self):
#         base = [sqrt(0.05), -sqrt(0.49), sqrt(0.15), sqrt(0.31)]
#         transformed = walsh_hadamard_transform(base)
#         sc_base = StateCoefficient(np.array([base]))
#         sc_transformed = StateCoefficient(np.array([transformed]) / 2)
#         p = sc_base.to_hadamard_probability()
#         p2 = sc_transformed.to_probability()
#         print(p.histogram)
#         print(p2.histogram)
#         self.assertDictEqual(p.histogram, p2.histogram)


class TestStateCoefficient(TestCase):
    def test_to_probability(self):
        base = [[sqrt(0.05), -sqrt(0.49)],
                [sqrt(0.15), sqrt(0.31)]]
        sc_base = StateCoefficient(np.array(base))
        p = sc_base.to_probability()
        values = []
        for i in range(0, 8):
            if i in p.histogram:
                values.append(p.histogram.get(i))
            else:
                values.append(0)
        result = [0.05, 0, 0, 0.49, 0.15, 0, 0.31, 0]
        np.testing.assert_array_almost_equal(values, result)


    def test_to_hadamard_probability(self):
        base = [[sqrt(0.05), -sqrt(0.49)],
                [sqrt(0.15), sqrt(0.31)]]
        sc_base = StateCoefficient(np.array(base))
        state = [sqrt(0.05), 0, 0, sqrt(0.49), sqrt(0.15), 0, sqrt(0.31), 0]
        transformed = walsh_hadamard_transform(state)/sqrt(8)
        p = sc_base.to_hadamard_probability()
        values = []
        a = 0
        for i in range(0, 8):
            if i in p.histogram:
                values.append(p.histogram.get(i))
                a = a + p.histogram.get(i)
            else:
                values.append(0)
        results = []
        a = 0
        for t in transformed:
            results.append(t * t)
            a = a + t * t
        np.testing.assert_array_almost_equal(values, results)


