from numpy import array
import math
from svd.core.algorithm import walsh_hadamard_transform
from svd.core.entity import Probability
from svd.core.encoder import Encoder


class History:
    def __init__(self, date, open_price, close_price):
        self.date = date
        self.open_price = open_price
        self.close_price = close_price


class StateCoefficient:
    def __init__(self, data: array):
        self.data = data

    def to_state(self):
        stock_dimension = math.ceil(math.log2(len(self.data)))
        time_dimension = math.ceil(math.log2(len(self.data[0])))
        n = stock_dimension + time_dimension
        results = {}
        for i, d in enumerate(self.data):
            data_num = pow(2, time_dimension) * i
            for j, value in enumerate(d):
                num = data_num + j
                results[num] = value
        rs = []
        for r in sorted(results.items(), key=lambda a : a[0]):
            rs.append(r[1])
        return rs

    def to_naive_probability(self):
        stock_dimension = math.ceil(math.log2(len(self.data)))
        time_dimension = math.ceil(math.log2(len(self.data[0])))
        n = stock_dimension + time_dimension
        result = Probability(n, Encoder(n))
        for i, d in enumerate(self.data):
            data_num = pow(2, time_dimension) * i
            for j, value in enumerate(d):
                num = data_num + j
                result.add(num, value * value)
        return result

    def to_probability(self) -> Probability:
        return self.do_to_probability(self.data)

    def do_to_probability(self, data) -> Probability:
        stock_dimension = math.ceil(math.log2(len(data)))
        time_dimension = math.ceil(math.log2(len(data[0])))
        n = stock_dimension + time_dimension
        encoder = Encoder(n)
        ancilla_encoder = Encoder(n + 1)
        result = Probability(n + 1, ancilla_encoder)
        for i, d in enumerate(data):
            data_num = pow(2, time_dimension) * i
            for j, value in enumerate(d):
                num = data_num + j
                bitarray = encoder.encode(num)
                if value < 0:
                    bitarray.append(1)
                else:
                    bitarray.append(0)
                num = ancilla_encoder.decode(bitarray)
                result.add(num, value * value)
        return result

    def to_hadamard_probability(self) -> Probability:
        stock_dimension = math.ceil(math.log2(len(self.data)))
        time_dimension = math.ceil(math.log2(len(self.data[0])))
        n = stock_dimension + time_dimension
        state_map = {}
        encoder = Encoder(n)
        ancilla_encoder = Encoder(n + 1)
        for i, d in enumerate(self.data):
            data_num = pow(2, time_dimension) * i
            for j, value in enumerate(d):
                num = data_num + j
                bit_array = encoder.encode(num)
                if value < 0:
                    bit_array.append(1)
                    value = -value
                else:
                    bit_array.append(0)
                num = ancilla_encoder.decode(bit_array)
                state_map[num] = value
        state = []
        for i in range(pow(2, n + 1)):
            v = 0
            if i in state_map:
                v = state_map[i]
            state.append(v)
        vector = walsh_hadamard_transform(state) / pow(2, (n + 1) / 2)
        result = Probability(n + 1, Encoder(n + 1))
        for i, v in enumerate(vector):
            result.add(i, v * v)
        return result

    def dimension(self, data):
        stock_dimension = math.ceil(math.log2(len(data)))
        time_dimension = math.ceil(math.log2(len(data[0])))
        return stock_dimension + time_dimension
