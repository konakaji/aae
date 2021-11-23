from aae.core.sampler import QiskitSampler, Converter
from aae.core.entity import Probability
from aae.core.encoder import Encoder
from abc import abstractmethod
import math


class Cost:
    @abstractmethod
    def value(self, sampler: QiskitSampler):
        return 0

    @abstractmethod
    def name(self):
        return "None"


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
