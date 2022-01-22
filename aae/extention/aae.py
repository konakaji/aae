from aae.core.circuit import *
from aae.core.entity import Coefficient
from aae.core.exact_cost import KLCost, MMDCost
from aae.core.gradient_cost import *
from aae.core.mapper import CoefficientMapper, CoefficientMapperPositive
from aae.core.optimizer import *
from aae.core.sampler import *
from aae.core.task import GradientOptimizationTask
from aae.core.monitor import ImageGenrator, TaskWatcher
from aae.extention.base import TrainingMethod, LoadingMethod
from qiskit import QuantumRegister, QuantumCircuit

Z_BASIS_FIGURE_PATH = "output/figure"
X_BASIS_FIGURE_PATH = "output/figure_second"

AAE_KEY = "AAE"
POSITIVE_AAE_KEY = "POSITIVE_AAE"


class AAETrainingMethodBase(TrainingMethod):
    def __init__(self, z_basis_image_path=None, x_basis_image_path=None,
                 n_shot=400, variance=0.25, iteration=200, lr=0.1, lr_scheduler=None):
        super().__init__()
        self.variance = variance
        self.n_shot = n_shot
        self.iteration = iteration
        self.z_basis_image_path = z_basis_image_path
        self.x_basis_image_path = x_basis_image_path
        if lr_scheduler is None:
            self.lr_scheduler = UnitLRScheduler(lr)
        else:
            self.lr_scheduler = lr_scheduler
        # later set
        self.real = True
        self.cost = None

    def build(self, data_sampler, coefficients, n, factory):
        additional_circuit = AllHadamardGates(n)
        optimizer = AdamOptimizer(self.lr_scheduler, maxiter=self.iteration)
        converter = CircuitAppender(additional_circuit)
        probability, hadamard_probability = self.get_mapper(data_sampler, n).map(Coefficient(coefficients))
        task, task_watcher, cost = self._build_task(probability, hadamard_probability, additional_circuit,
                                                    converter, data_sampler, factory, optimizer)
        self.task_watcher = task_watcher
        self.cost = cost
        return task

    def get_cost(self, data_sampler):
        if self.cost is None:
            return 0
        return self.cost(data_sampler)

    @abstractmethod
    def get_mapper(self, data_sampler, n):
        pass

    def _build_task(self, probability, another_probability, additional_circuit,
                    converter, data_sampler, factory, optimizer):
        encoder = data_sampler.encoder
        mmd_gradient_cost = self._build_gradient_cost(probability, another_probability, additional_circuit,
                                                      encoder)
        # costs used just for displaying (computed by using state_vector)
        kl_cost = KLCost(probability, encoder)
        another_kl_cost = KLCost(another_probability, encoder, converter)
        mmd_cost = MMDCost(probability, encoder)
        mmd_cost.custom_kernel = self._gaussian_kernel()
        another_mmd_cost = MMDCost(another_probability, encoder, CircuitAppender(additional_circuit))
        another_mmd_cost.custom_kernel = self._gaussian_kernel()
        image_generators = []
        if self.z_basis_image_path is not None and self.x_basis_image_path is not None:
            image_generators = [ImageGenrator(self.z_basis_image_path, probability),
                                ImageGenrator(self.x_basis_image_path, another_probability,
                                              converter=converter)]
        task_watcher = TaskWatcher(image_generators,
                                   [kl_cost, another_kl_cost, mmd_cost, another_mmd_cost])

        def total_cost(sampler):
            z_basis = mmd_cost.value(sampler)
            x_basis = another_mmd_cost.value(sampler)
            return z_basis + x_basis

        return GradientOptimizationTask(data_sampler, factory, mmd_gradient_cost,
                                        task_watcher, self.n_shot, optimizer), task_watcher, total_cost

    def _build_gradient_cost(self, probability, another_probability, additional_circuit,
                             encoder, cutoff=1):
        mmd_gradient_cost = MultipleMMDGradientCost(probability, another_probability,
                                                    additional_circuit, encoder,
                                                    lambda_1=0.5, lambda_2=0.5)
        mmd_gradient_cost.custom_kernel = self._gaussian_kernel()
        mmd_gradient_cost.cutoff = cutoff
        return mmd_gradient_cost

    def _gaussian_kernel(self):
        def result(x, y):
            return math.exp(-pow(x - y, 2) / self.variance)

        return result


class AAETrainingMethod(AAETrainingMethodBase):
    def get_mapper(self, data_sampler, n):
        return CoefficientMapper(n - 1, Encoder(n - 1), data_sampler.encoder)

    @classmethod
    def get_name(cls):
        return AAE_KEY


class AAELoadingMethod(LoadingMethod):
    def add_data_gates(self, sampler, q_circuit: QuantumCircuit):
        c = sampler.circuit.merge(q_circuit)
        return Hadamard(0).merge(c)

    def get_state_vector(self, sampler):
        sampler.circuit.additional_circuit = Hadamard(0)
        sampler.post_select = {0: 1}
        v = sampler.get_state_vector()
        sampler.post_select = {}
        sampler.circuit.additional_circuit = None
        v = self._post_select(v, sampler.n_qubit - 1, 1, sampler.n_qubit)
        return v

    @classmethod
    def _post_select(cls, state_vector, i, bit, n_qubit):
        results = []
        encoder = Encoder(n_qubit)
        norm = 0
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
            norm = norm + amplitude * amplitude.conjugate()
        finals = []
        norm = math.sqrt(norm)
        for r in results:
            finals.append(r / norm)
        return finals

    @classmethod
    def _is_correct(cls, state_vector, i, bit, n_qubit):
        encoder = Encoder(n_qubit)
        for num, amplitude in enumerate(state_vector):
            array = encoder.encode(num)
            if array[i] != bit and amplitude != 0:
                return False
        return True


class PostSelectJobFuture:
    def __init__(self, execute, qc: Gates, n: int, post_select: {}, n_shot: int):
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


class AAEUtil:
    @classmethod
    def execute_with_post_selection(self, qc: qiskit.QuantumCircuit, backend, shots: int, n, initial_layout=None,
                                    extra=2.5):
        def execute():
            job = qiskit.execute(qc, backend, shots=int(shots * extra), initial_layout=initial_layout)
            return job

        return PostSelectJobFuture(execute, qc, n=n, post_select={n - 1: 1}, n_shot=shots)


class PositiveAAETrainingMethod(AAETrainingMethodBase):
    def get_mapper(self, data_sampler, n):
        return CoefficientMapperPositive(n, data_sampler.encoder)

    @classmethod
    def get_name(cls):
        return POSITIVE_AAE_KEY
