from aae.core.encoder import Encoder
from aae.core.sampler import ParametrizedDefaultSamplerFactory, QISKIT, QULACS
from aae.extention.base import TrainingMethod
from ibmq.allocator import NaiveQubitAllocator
from qwrapper.circuit import QWrapper as QuantumCircuit
from aae.extention.context import Context

ENERGY_KEY = "final-energy"
LAYER_KEY = "layer"
NAME_KEY = "training-method"


class DataLearning:
    def __init__(self, n_qubit: int, layer: int, factory=None, type=QISKIT):
        self.n = n_qubit
        self.layer = layer
        if factory is None:
            self.factory = ParametrizedDefaultSamplerFactory(self.layer, self.n, type)
        else:
            self.factory = factory
        self.sampler = None
        self.type = type
        self.final_cost = None
        self.task_watcher = None
        self.training_method = None
        self.load_method = None

    def load(self, filename, device=None, allocator=None, reservation=False):
        self.sampler = self.factory.load(filename, self.type)
        self.load_method = Context.get(self.factory.get_extra(filename)[NAME_KEY])
        if device is not None:
            from ibmq.base import DeviceFactory
            if allocator is None:
                allocator = NaiveQubitAllocator(self.n)
            device_factory = DeviceFactory(device, reservation=reservation)
            self.sampler.simulator = device_factory.get_backend()
            self.sampler.factory = device_factory
            self.sampler.circuit.layout = allocator.allocate(self.sampler.simulator.configuration().coupling_map)

    def learn(self, coefficients: [float], device=None,
              reservation=False, allocator=None, training_method: TrainingMethod = None):
        data_sampler = self._get_data_sampler(training_method)
        self._set_device(data_sampler, allocator, device, reservation)
        data_sampler.encoder = Encoder(self.n)
        optimization = training_method.build(data_sampler, coefficients, self.n, self.factory)
        optimization.optimize()
        self.sampler = data_sampler
        self.training_method = training_method
        self.load_method = Context.get(training_method.get_name())
        result = self.get_state_vector()
        return result

    def add_data_gates(self, q_circuit: QuantumCircuit):
        return self.load_method.add_data_gates(self.sampler, q_circuit)

    def get_state_vector(self):
        return self.load_method.get_state_vector(self.sampler)

    def save_model(self, path):
        cost = self.training_method.get_cost(self.sampler)
        name = self.training_method.get_name()
        self.factory.save(path, self.sampler,
                          {ENERGY_KEY: cost,
                           LAYER_KEY: self.layer, NAME_KEY: name})

    def save_cost_transition(self, path):
        self.training_method.task_watcher.save_energy(path)

    def _get_data_sampler(self, method):
        if self.sampler is None:
            if method.real:
                data_sampler = self.factory.generate_real_he(method.idblock)
            else:
                data_sampler = self.factory.generate_he()
        else:
            data_sampler = self.sampler
        return data_sampler

    def _set_device(self, data_sampler, allocator, device, reservation):
        if device is not None:
            from ibmq.base import DeviceFactory
            if allocator is None:
                allocator = NaiveQubitAllocator(self.n)
            device_factory = DeviceFactory(device, reservation=reservation)
            data_sampler.simulator = device_factory.get_backend()
            data_sampler.factory = device_factory
            data_sampler.circuit.layout = allocator.allocate(data_sampler.simulator.configuration().coupling_map)
