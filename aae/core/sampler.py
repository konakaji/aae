from abc import ABC, abstractmethod
from aae.core.exception import IllegalArgumentException
from aae.core.entity import Sample
from aae.core.encoder import Encoder
from aae.core.circuit import QISKIT, QULACS, Gates, \
    RandomGates, TENCircuitFactory, HECircuitFactory, plus_circuit, minus_circuit
from ibmq.base import DeviceFactory
from qwrapper.circuit import QiskitCircuit, QulacsCircuit, QWrapper
import json


class Sampler(ABC):
    @abstractmethod
    def sample(self, n_shot) -> [Sample]:
        pass

    @abstractmethod
    def exact_probabilities(self):
        pass


# class SampleJobFuture:
#     def __init__(self, job, listener):
#         self.job = job
#         self.listener = listener
#         self.result = None
#
#     def get(self):
#         if self.result is not None:
#             return self.result
#         try:
#             job_result = self.job.result()
#
#         except qiskit.exceptions.QiskitError as e:
#             raise SamplerException(e)
#         self.result = self.listener(job_result)
#         return self.result


class SamplerException(Exception):
    pass


class DefaultSampler(Sampler):
    def __init__(self, circuit: Gates, n_qubit, type=QISKIT):
        self.circuit = circuit
        self.encoder = Encoder(n_qubit)
        self.type = type
        self.n_qubit = n_qubit
        self.factory: DeviceFactory = None
        self.post_select = {}
        self.max_retry = 5

    def recover(self):
        if self.factory is not None:
            self.simulator = self.factory.get_backend()

    def draw(self, output='mpl'):
        qc = self._build_circuit()
        qc.draw(output=output)

    def sample(self, n_shot):
        qc = self._build_circuit()
        return qc.get_async_samples(n_shot)

    def exact_probabilities(self):
        results = {}
        partial_qubits = self.n_qubit - len(self.post_select)
        partial_encoder = Encoder(partial_qubits)
        qc = self._build_circuit()
        for k, v in self.post_select.items():
            qc.post_select(k, v)
        statevector = qc.get_state_vector()
        for num, c in enumerate(statevector):
            bit_array = self.encoder.encode(num)
            for k, v in sorted(self.post_select.items(), key=lambda a: a[0], reverse=True):
                bit_array.pop(self.n_qubit - k - 1)
            key = partial_encoder.decode(bit_array)
            results[key] = abs(c * c.conjugate())
        rs = []
        for _, p in sorted(results.items(), key=lambda a: a[0]):
            rs.append(p)
        return rs

    def get_state_vector(self):
        qc = self._build_circuit()
        for k, v in self.post_select.items():
            qc.post_select(k, v)
        return qc.get_state_vector()

    def add_post_select(self, qubit_index, qubit_value):
        self.post_select[qubit_index] = qubit_value

    def _all_register(self):
        r = []
        for i in range(self.n_qubit):
            r.append(i)
        return r

    def _build_circuit(self) -> QWrapper:
        if self.type == QISKIT:
            qc = QiskitCircuit(self.n_qubit)
        elif self.type == QULACS:
            qc = QulacsCircuit(self.n_qubit)
        else:
            raise IllegalArgumentException("the type {} does not exist.".format(self.type))
        self.circuit.merge(qc)
        return qc


class Parametrized(ABC):
    @abstractmethod
    def get_parameters(self):
        return []

    @abstractmethod
    def copy(self, parameters):
        pass


class ParametrizedDefaultSampler(Parametrized, DefaultSampler):
    def __init__(self, circuit: RandomGates, n_qubit, type=QISKIT):
        super().__init__(circuit, n_qubit, type)
        self.circuit = circuit

    def get_parameters(self):
        return self.circuit.parameters

    def copy(self, parameters):
        self.circuit.copy(parameters)

    def name(self):
        return "ParametrizedQiskitSampler"


class ParametrizedDefaultSamplerFactory:
    def __init__(self, layer_count, n_qubit, type):
        self.layer_count = layer_count
        self.n_qubit = n_qubit
        self.type = type

    def plus_sampler(self, sampler: ParametrizedDefaultSampler, index):
        circuit = plus_circuit(sampler.circuit, index)
        return ParametrizedDefaultSampler(circuit, circuit.n_qubit, self.type)

    def minus_sampler(self, sampler: ParametrizedDefaultSampler, index):
        circuit = minus_circuit(sampler.circuit, index)
        return ParametrizedDefaultSampler(circuit, circuit.n_qubit, self.type)

    def generate_he(self):
        circuit = HECircuitFactory.generate(self.layer_count, self.n_qubit)
        return self._create_instance(circuit)

    def generate_real_he(self, idblock=False):
        if idblock:
            circuit = HECircuitFactory.generate_real_idblock(self.layer_count, self.n_qubit)
        else:
            circuit = HECircuitFactory.generate_real(self.layer_count, self.n_qubit)
        return self._create_instance(circuit)

    def generate_ten(self, n_a, n_b):
        circuit = TENCircuitFactory.generate(self.layer_count, self.n_qubit, n_a, n_b)
        return self._create_instance(circuit)

    def save(self, filename, sampler: ParametrizedDefaultSampler, extra: {}):
        with open(filename, "w") as f:
            directions = []
            parameters = []
            for i, p in enumerate(sampler.circuit.parameters):
                directions.append(sampler.circuit.directions[i])
                parameters.append(p)
            result = {"name": sampler.name(),
                      "directions": directions,
                      "parameters": parameters,
                      "circuit": sampler.circuit.key(),
                      "extra": extra,
                      "n_qubit": self.n_qubit}
            f.write(json.dumps(result, indent=2))

    def load(self, filename, type):
        with open(filename) as f:
            map = json.loads(f.read())
            directions = map["directions"]
            parameters = map["parameters"]
            layer_count = int(len(parameters)/self.n_qubit)
            self.layer_count = layer_count
            n_qubit = map["n_qubit"]
            c_key = map["circuit"]
            if c_key == "idblock":
                circuit = HECircuitFactory.do_generate_idblock(parameters, directions, n_qubit)
            else:
                circuit = HECircuitFactory.do_generate(parameters, directions, n_qubit)
            return self._create_instance(circuit, type)

    def get_extra(self, filename):
        with open(filename) as f:
            map = json.loads(f.read())
            return map["extra"]

    def create_instance(self, circuit):
        return ParametrizedDefaultSampler(circuit, self.n_qubit, self.type)

    def _create_instance(self, circuit, type=None):
        if type is None:
            type = self.type
        return ParametrizedDefaultSampler(circuit, self.n_qubit, type)


class Converter:
    def convert(self, sampler: Sampler):
        return sampler

    def revoke(self, sampler: Sampler):
        return sampler


class CircuitAppender(Converter):
    def __init__(self, circuit: Gates):
        self.circuit = circuit

    def convert(self, sampler: ParametrizedDefaultSampler):
        sampler.circuit.additional_circuit = self.circuit
        return sampler

    def revoke(self, sampler: Sampler):
        sampler.circuit.additional_circuit = None
