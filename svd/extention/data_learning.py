import math
from svd.core.mapper import CoefficientMapper
from svd.core.entity import Coefficient
from svd.core.encoder import Encoder
from svd.core.sampler import ParametrizedQiskitSamplerFactory, ParametrizedQiskitSampler, Sampler, Converter
from svd.core.optimizer import AdamOptimizer, UnitLRScheduler
from svd.core.circuit import AllHadamardCircuit, QiskitCircuit, HadamardAndMeausre
from svd.core.task import AdamGradientOptimizationTask
from svd.core.gradient_cost import MultipleMMDGradientCost
from svd.core.exact_cost import KLCost, MMDCost
from svd.core.util import TaskWatcher, ImageGenrator
import time, qiskit, random

ENERGY_KEY = "final-energy"
LAYER_KEY = "layer"
OPTIMIZATION_FIGURE_PATH = "output/figure"
SECOND_OPTIMIZATION_FIGURE_PATH = "output/figure_second"
MODEL_PATH = "output/data_model"
ENERGY_PATH = "output/energy"


class DataLearning:
    def __init__(self, n_qubit: int, layer: int):
        self.n = n_qubit
        self.layer = layer
        self.factory = ParametrizedQiskitSamplerFactory(self.layer, self.n)
        self.sampler = None

    def load(self, filename):
        self.sampler = self.factory.load(MODEL_PATH + "/" + filename)

    def add_data_gates(self, q_circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        qc, q_register = self.sampler.circuit.merge(q_circuit, q_register)
        return HadamardAndMeausre(0).merge(qc, q_register)[0]

    def execute_with_post_selection(self, qc: qiskit.QuantumCircuit, backend, shots: int, initial_layout=None,
                                    extra=2.5):
        def execute():
            job = qiskit.execute(qc, backend, shots=int(shots * extra), initial_layout=initial_layout)
            return job

        return PostSelectJobFuture(execute, qc, n=self.n, post_select={self.n - 1: 1}, n_shot=shots)

    def get_state_vector(self):
        while True:
            self.sampler.circuit.additional_circuit = HadamardAndMeausre(0)
            self.sampler.post_select = {0: 1}
            v = self.sampler.get_state_vector()
            correct = self._is_correct(v, self.n - 1, 1, self.n)
            if correct:
                return self._post_select(v, self.n - 1, 1, self.n)

    def learn(self, coefficients: [float], device=None, filename="default-" + str(int(time.time())),
              reservation=False, n_shot=400, variance=0.25, iteration=200, lr_scheduler=UnitLRScheduler(0.1),
              dry=False):
        encoder = Encoder(self.n)
        mapper = CoefficientMapper(self.n - 1, Encoder(self.n - 1), encoder)
        probability, hadamard_probability = mapper.map(Coefficient(coefficients))
        data_sampler = self.factory.generate_real_he()
        data_sampler.encoder = encoder
        if device is not None:
            from ibmq.base import DeviceFactory
            device_factory = DeviceFactory(device, reservation=reservation)
            data_sampler.simulator = device_factory.get_backend()
            data_sampler.factory = device_factory
        optimizer = AdamOptimizer(lr_scheduler, maxiter=iteration)
        additional_circuit = AllHadamardCircuit(self.n)
        converter = CircuitAppender(additional_circuit)
        optimization, total_cost = self._build_task(probability, hadamard_probability, additional_circuit, encoder,
                                                    converter, data_sampler,
                                                    self.factory,
                                                    optimizer, variance, n_shot)
        optimization.optimize()
        # save the progress to the file
        if not dry:
            optimization.task_watcher.save(ENERGY_PATH + "/" + filename)
            # save the model to the file
            self.factory.save(MODEL_PATH + "/" + filename, data_sampler,
                              {ENERGY_KEY: total_cost(data_sampler),
                               LAYER_KEY: self.layer})
        self.sampler = data_sampler
        return self.get_state_vector()

    def _build_task(self, probability, another_probability, additional_circuit, encoder,
                    converter, data_sampler, factory, optimizer, variance, nshot):
        mmd_gradient_cost = self._build_gradient_cost(probability, another_probability, additional_circuit,
                                                      encoder)
        # costs used just for displaying (computed by using state_vector)
        kl_cost = KLCost(probability, encoder)
        another_kl_cost = KLCost(another_probability, encoder, converter)
        mmd_cost = MMDCost(probability, encoder)
        mmd_cost.custom_kernel = gaussian_kernel(variance)
        another_mmd_cost = MMDCost(another_probability, encoder, CircuitAppender(additional_circuit))
        task_watcher = TaskWatcher([ImageGenrator(OPTIMIZATION_FIGURE_PATH, probability),
                                    ImageGenrator(SECOND_OPTIMIZATION_FIGURE_PATH, another_probability,
                                                  converter=converter)],
                                   [kl_cost, another_kl_cost, mmd_cost, another_mmd_cost])

        def total_cost(sampler):
            return mmd_cost.value(sampler) + another_mmd_cost.value(data_sampler)

        return AdamGradientOptimizationTask(data_sampler, factory, mmd_gradient_cost,
                                            task_watcher, nshot, optimizer), total_cost

    def _build_gradient_cost(self, probability, another_probability, additional_circuit,
                             encoder, cutoff=1, variance=0.25):
        mmd_gradient_cost = MultipleMMDGradientCost(probability, another_probability,
                                                    additional_circuit, encoder,
                                                    lambda_1=0.5, lambda_2=0.5)
        mmd_gradient_cost.custom_kernel = gaussian_kernel(variance)
        mmd_gradient_cost.cutoff = cutoff
        return mmd_gradient_cost

    def _post_select(self, state_vector, i, bit, n_qubit):
        results = []
        encoder = Encoder(n_qubit)
        for num, amplitude in enumerate(state_vector):
            array = encoder.encode(num)
            if array[i] != bit:
                continue
            new_array = []
            for j, a in enumerate(array):
                if j == i:
                    continue
                new_array.append(a)
            results.append(amplitude)
        return results

    def _is_correct(self, state_vector, i, bit, n_qubit):
        encoder = Encoder(n_qubit)
        for num, amplitude in enumerate(state_vector):
            array = encoder.encode(num)
            if array[i] != bit and amplitude != 0:
                return False
        return True


class CircuitAppender(Converter):
    def __init__(self, circuit: QiskitCircuit):
        self.circuit = circuit

    def convert(self, sampler: ParametrizedQiskitSampler):
        sampler.circuit.additional_circuit = self.circuit
        return sampler

    def revoke(self, sampler: Sampler):
        sampler.circuit.additional_circuit = None


class PostSelectJobFuture:
    def __init__(self, execute, qc: QiskitCircuit, n: int, post_select: {}, n_shot: int):
        self.n_shot = n_shot
        self.execute = execute
        self.qc = qc
        self.encoder = Encoder(n)
        self.post_select = post_select
        self.job = execute()

    def get(self, samples=[]):
        samples.extend(self._do_get())
        if len(samples) >= self.n_shot:
            return self._finalize(samples)
        return self.get(samples)

    def _finalize(self, samples):
        random.shuffle(samples)
        return samples[0: len(samples)]

    def _do_get(self):
        result = self.job.result().get_counts(self.qc)
        samples = []
        for bitstring, count in result.items():
            add = True
            bitarray = self.encoder.to_bitarray(bitstring)
            for q_index, q_value in sorted(self.post_select.items(), key=lambda a: a[0], reverse=True):
                if bitarray.pop(q_index) != q_value:
                    add = False
            if add:
                for i in range(count):
                    samples.append(bitarray)
        return samples


def gaussian_kernel(variance):
    def result(x, y):
        return math.exp(-pow(x - y, 2) / variance)

    return result
