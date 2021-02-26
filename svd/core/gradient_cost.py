from svd.core.entity import Probability
from svd.core.sampler import ParametrizedQiskitSampler, ParametrizedQiskitSamplerFactory, SamplerException
from svd.core.circuit import QiskitCircuit
from svd.core.encoder import Encoder
from svd.core.entity import Sample
import numpy, math


class GradientCost:
    def sample_gradient(self, sampler: ParametrizedQiskitSampler,
                        factory: ParametrizedQiskitSamplerFactory, n_shot):
        return []


class InvalidStateException(Exception):
    pass


class MMDGradientCost(GradientCost):
    def __init__(self, probability: Probability, encoder: Encoder):
        self.probability = probability
        self.encoder = encoder
        self.custom_kernel = None
        self.cutoff = 0
        self.max_retry = 5

    def sample_gradient(self, sampler: ParametrizedQiskitSampler,
                        factory: ParametrizedQiskitSamplerFactory, n_shot):
        return self.do_sample_gradient(sampler, factory, n_shot, self.probability)

    def do_sample_gradient(self, sampler: ParametrizedQiskitSampler,
                           factory: ParametrizedQiskitSamplerFactory, n_shot, probability: Probability, retry=0):
        if retry == self.max_retry:
            raise InvalidStateException("retry limit exceed")
        results = numpy.zeros((len(sampler.get_parameters())), float)
        future = sampler.sample(n_shot)
        pls_futures = []
        minus_futures = []
        for j in range(len(results)):
            plus_sampler = factory.plus_sampler(sampler, j)
            plus_sampler.circuit.additional_circuit = sampler.circuit.additional_circuit
            minus_sampler = factory.minus_sampler(sampler, j)
            minus_sampler.circuit.additional_circuit = sampler.circuit.additional_circuit
            pls_futures.append(plus_sampler.sample(n_shot))
            minus_futures.append(minus_sampler.sample(n_shot))
        try:
            samples = future.get()
            for j in range(len(results)):
                pls = pls_futures[j].get()
                mis = minus_futures[j].get()
                result = self._compute_gradient(samples, pls, mis, n_shot, probability)
                results[j] = result / len(samples)
        except SamplerException as e:
            sampler.recover()
            print("error, retrying", e)
            return self.do_sample_gradient(sampler, factory, n_shot, probability, retry + 1)
        return results

    def _compute_gradient(self, samples, pls, mis, n_shot, probability: Probability):
        result = 0
        for i in range(n_shot):
            s = samples[i]
            result = result + self.kernel(pls[i], s)
            result = result - self.kernel(mis[i], s)
            for j in range(self.cutoff_values(pls[i])[0], self.cutoff_values(pls[i])[1]):
                result = result - probability.get(j) * self.kernel(pls[i], Sample(self.encoder.encode(j)))
            for j in range(self.cutoff_values(mis[i])[0], self.cutoff_values(mis[i])[1]):
                result = result + probability.get(j) * self.kernel(mis[i], Sample(self.encoder.encode(j)))
        return result

    def kernel(self, x, y):
        if self.custom_kernel is not None:
            return self.custom_kernel(self.encoder.decode(x.data), self.encoder.decode(y.data))
        if x == y:
            return 1
        else:
            return 0

    def cutoff_values(self, x):
        decoded = self.encoder.decode(x.data)
        return max(decoded - self.cutoff, 0), min(decoded + self.cutoff + 1, pow(2, self.probability.N))


class MultipleMMDGradientCost(MMDGradientCost):
    def __init__(self, probability: Probability,
                 another_probability: Probability, another_circuit: QiskitCircuit, encoder: Encoder, lambda_1=0.5,
                 lambda_2=0.5):
        self.probability = probability
        self.another_probability = another_probability
        self.another_circuit = another_circuit
        self.lambda_1 = lambda_1
        self.lambda_2 = lambda_2
        super().__init__(probability, encoder)

    def sample_gradient(self, sampler: ParametrizedQiskitSampler,
                        factory: ParametrizedQiskitSamplerFactory, n_shot):
        sampler.circuit.additional_circuit = None
        base_gradient = super().do_sample_gradient(sampler, factory, n_shot, self.probability)
        sampler.circuit.additional_circuit = self.another_circuit
        another_gradient = super().do_sample_gradient(sampler, factory, n_shot, self.another_probability)
        sampler.circuit.additional_circuit = None
        return self.lambda_1 * base_gradient + self.lambda_2 * another_gradient
