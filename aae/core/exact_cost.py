from aae.core.sampler import QiskitSampler, Converter
from aae.core.entity import Probability
from aae.core.encoder import Encoder
import math


class Cost:
    def value(self, sampler: QiskitSampler):
        return 0

    def name(self):
        return "None"


class SVDExactCost(Cost):
    def __init__(self, n_a, n_b, encoder: Encoder):
        self.n_a = n_a
        self.n_b = n_b
        self.encoder = encoder

    def value(self, sampler: QiskitSampler):
        n = min(self.n_a, self.n_b)
        result = 0
        for i, p in enumerate(sampler.exact_probabilities()):
            bit_array = self.encoder.encode(i)
            for k in range(n):
                b = bit_array[k]
                b2 = bit_array[self.n_a + k]
                v = -1
                if b == b2:
                    v = 1
                result = result + p * (1 - v) / 2
        return result


class MMDCost(Cost):
    def __init__(self, probability: Probability, encoder: Encoder, converter: Converter = None):
        self.probability = probability
        self.encoder = encoder
        self.converter = converter
        self.custom_kernel = None

    def value(self, sampler: QiskitSampler):
        if self.converter is not None:
            sampler = self.converter.convert(sampler)
        result = 0
        for x, qx in enumerate(sampler.exact_probabilities()):
            for y, qy in enumerate(sampler.exact_probabilities()):
                result = result + self.kernel(x, y) * self.probability.get(x) \
                         * self.probability.get(y)
                result = result + self.kernel(x, y) * qx * qy
                result = result - 2 * self.kernel(x, y) * self.probability.get(x) * qy
        if self.converter is not None:
            self.converter.revoke(sampler)
        return result

    def name(self):
        if self.converter is not None:
            return "MMDCost(Converted)"
        else:
            return "MMDCost(Non-Converted)"

    def kernel(self, x, y):
        if self.custom_kernel is not None:
            return self.custom_kernel(x, y)
        if x == y:
            return 1
        else:
            return 0


class KLCost(Cost):
    def __init__(self, probability: Probability, encoder: Encoder, converter: Converter = None):
        self.probability = probability
        self.encoder = encoder
        self.converter = converter

    def value(self, sampler: QiskitSampler):
        if self.converter is not None:
            sampler = self.converter.convert(sampler)
        qs = sampler.exact_probabilities()
        result = 0
        for x, q in enumerate(qs):
            p = self.probability.value(self.encoder.encode(x))
            cost = 1
            if q != 0:
                cost = - p * math.log(q)
            result = result + cost
            if p > 0:
                result = result + p * math.log(p)
        if self.converter is not None:
            self.converter.revoke(sampler)
        return result

    def name(self):
        if self.converter is not None:
            return "KLCost(Converted)"
        return "KLCost(Non-Converted)"
