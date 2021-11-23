from aae.core.encoder import Encoder


class Sample:
    def __init__(self, bit_array):
        self.data = bit_array

    def __eq__(self, sample):
        for i, b in enumerate(self.data):
            s = sample.data[i]
            if s != b:
                return False
        return True

    def __repr__(self):
        return str(self.data)


class Coefficient:
    def __init__(self, data):
        self.data = data


class Probability:
    def __init__(self, N, encoder: Encoder):
        self.N = N
        self.encoder = encoder
        self.histogram = {}

    def __repr__(self):
        result = ""
        for i in range(pow(2, self.N)):
            value = 0
            if i in self.histogram:
                value = self.histogram[i]
            result = result + "{},{}\n".format(i, value)
        return result

    def norm(self):
        r = 0
        for k, v in self.histogram.items():
            r = r + v
        return r

    def add(self, num, value):
        self.histogram[num] = value

    def value(self, bit_array):
        x = self.encoder.decode(bit_array)
        if not x in self.histogram:
            return 0
        return self.histogram[x]

    def get(self, x):
        if x in self.histogram:
            return self.histogram[x]
        return 0

    def plot(self, title=None):
        import matplotlib.pyplot as plt
        xs = []
        ys = []
        for x in range(pow(2, self.N)):
            xs.append(x)
            ys.append(self.value(self.encoder.encode(x)))
        if title is None:
            title = "target"
        plt.bar(xs, ys, color='c', label=title)

    def plot_state(self, exact_probabilities, title=None):
        import matplotlib.pyplot as plt
        xs = []
        ys = []
        for x, v in enumerate(exact_probabilities):
            xs.append(x)
            ys.append(v)
        if title is None:
            title = "trained"
        plt.plot(xs, ys, color='green', marker=".", markersize=10, label=title)
