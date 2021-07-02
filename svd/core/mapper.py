from svd.core.encoder import Encoder
from svd.core.entity import Coefficient, Probability
from svd.core.algorithm import walsh_hadamard_transform


class CoefficientMapperAllpos:
    def __init__(self, n, encoder: Encoder):
        self.n = n
        self.encoder = encoder

    def map(self, coefficient: Coefficient) -> (Probability, Probability):
        p1 = self._do_map(coefficient)
        p2 = self._do_map_hadamard(coefficient)
        return p1, p2

    def _do_map(self, coefficient):
        result = Probability(self.n + 0, self.encoder)
        for num, value in enumerate(coefficient.data):
            bitarray = self.encoder.encode(num)
            num = self.encoder.decode(bitarray)
            result.add(num, value * value)
        return result

    def _do_map_hadamard(self, coefficient):
        state_map = {}
        for num, value in enumerate(coefficient.data):
            bit_array = self.encoder.encode(num)
            num = self.encoder.decode(bit_array)
            state_map[num] = value
        state = []
        for i in range(pow(2, self.n + 0)):
            v = 0
            if i in state_map:
                v = state_map[i]
            state.append(v)
        vector = walsh_hadamard_transform(state) / pow(2, (self.n + 0) / 2)
        result = Probability(self.n + 0, Encoder(self.n + 0))
        for i, v in enumerate(vector):
            result.add(i, v * v)
        return result


class CoefficientMapper:
    def __init__(self, n, encoder: Encoder, ancilla_encoder: Encoder):
        self.n = n
        self.encoder = encoder
        self.ancilla_encoder = ancilla_encoder

    def map(self, coefficient: Coefficient) -> (Probability, Probability):
        p1 = self._do_map(coefficient)
        p2 = self._do_map_hadamard(coefficient)
        return p1, p2

    def _do_map(self, coefficient):
        result = Probability(self.n + 1, self.ancilla_encoder)
        for num, value in enumerate(coefficient.data):
            bitarray = self.encoder.encode(num)
            if value < 0:
                bitarray.append(1)
            else:
                bitarray.append(0)
            num = self.ancilla_encoder.decode(bitarray)
            result.add(num, value * value)
        return result

    def _do_map_hadamard(self, coefficient):
        state_map = {}
        for num, value in enumerate(coefficient.data):
            bit_array = self.encoder.encode(num)
            if value < 0:
                bit_array.append(1)
                value = -value
            else:
                bit_array.append(0)
            num = self.ancilla_encoder.decode(bit_array)
            state_map[num] = value
        state = []
        for i in range(pow(2, self.n + 1)):
            v = 0
            if i in state_map:
                v = state_map[i]
            state.append(v)
        vector = walsh_hadamard_transform(state) / pow(2, (self.n + 1) / 2)
        result = Probability(self.n + 1, Encoder(self.n + 1))
        for i, v in enumerate(vector):
            result.add(i, v * v)
        return result
