from aae.core.sampler import DefaultSampler, Converter
from aae.core.entity import Probability
from aae.core.encoder import Encoder
from aae.core.circuit import Hadamard
from abc import abstractmethod
import math, numpy as np


class Cost:
    @abstractmethod
    def value(self, sampler: DefaultSampler):
        return 0

    @abstractmethod
    def name(self):
        return "None"


class OverlapCost(Cost):
    def __init__(self, coefficient):
        self.coefficient = np.array(coefficient)

    def value(self, sampler: DefaultSampler):
        encoder = Encoder(sampler.n_qubit)
        sampler.circuit.additional_circuit = Hadamard(0)
        sampler.post_select = {0: 1}
        result = []
        for j, v in enumerate(sampler.get_state_vector()):
            array = encoder.encode(j)
            if array[sampler.n_qubit - 1] == 0:
                continue
            result.append(v)
        sampler.circuit.additional_circuit = None
        sampler.post_select = {}
        return abs(np.array(result).dot(self.coefficient))

    def name(self):
        return "OverlapCost"


class MMDCost(Cost):
    def __init__(self, probability: Probability, encoder: Encoder, converter: Converter = None):
        self.probability = probability
        self.encoder = encoder
        self.converter = converter
        self.custom_kernel = None

    def value(self, sampler: DefaultSampler):
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

    def value(self, sampler: DefaultSampler):
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
