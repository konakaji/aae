from svd.core.entity import Sample
from svd.core.exact_cost import Cost
from svd.core.sampler import Sampler


class SampleCost(Cost):
    def __init__(self, n_shot):
        self.n_shot = n_shot

    def value(self, sampler: Sampler):
        return self.compute(sampler.sample(self.n_shot))

    def compute(self, samples: [Sample]):
        result = 0
        for sample in samples:
            result = result + self.do_compute(sample)
        return result/len(samples)

    def do_compute(self, sample: Sample):
        return 0


class SVDSampleCost(SampleCost):
    def __init__(self, na, nb, n_shot):
        super().__init__(n_shot)
        self.na = na
        self.nb = nb

    def do_compute(self, sample: Sample):
        if self.na < self.nb:
            n = self.na
        else:
            n = self.nb
        result = 0
        for i in range(n):
            z_spin_a = 2 * (sample.data[i] - 0.5)
            z_spin_b = 2 * (sample.data[self.na + i] - 0.5)
            result = result + (1 - z_spin_a * z_spin_b) / 2
        return result
