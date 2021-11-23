from aae.core.entity import Sample
from aae.core.encoder import Encoder
from aae.core.circuit import QiskitCircuit, \
    RandomCircuit, TENCircuit, TENCircuitFactory, HECircuitFactory, plus_circuit, minus_circuit
from ibmq.base import DeviceFactory
import qiskit, random, json


class Sampler:
    def sample(self, n_shot) -> [Sample]:
        return []

    def exact_probabilities(self):
        return []

    def exact_partial_probabilities(self, partial_qubit):
        return []


class SampleJobFuture:
    def __init__(self, job, listener):
        self.job = job
        self.listener = listener
        self.result = None

    def get(self):
        if self.result is not None:
            return self.result
        try:
            job_result = self.job.result()

        except qiskit.exceptions.QiskitError as e:
            raise SamplerException(e)
        self.result = self.listener(job_result)
        return self.result


class SamplerException(Exception):
    pass


class QiskitSampler(Sampler):
    def __init__(self, circuit: QiskitCircuit, n_qubit):
        self.circuit = circuit
        self.encoder = Encoder(n_qubit)
        self.n_qubit = n_qubit
        self.simulator = qiskit.Aer.get_backend("qasm_simulator")
        self.state_simulator = qiskit.Aer.get_backend("statevector_simulator")
        self.factory: DeviceFactory = None
        self.sync = False
        self.post_select = {}
        self.max_retry = 5

    def recover(self):
        if self.factory is not None:
            self.simulator = self.factory.get_backend()

    def draw(self, output='mpl', style=None, registers=None):
        qc, q_register = self._build_circuit()
        if registers is None:
            registers = self._all_register()
        qc.measure(registers, registers)
        qc.draw(output=output, fold=-1, style=style, plot_barriers=False)

    def sample(self, n_shot) -> SampleJobFuture:
        if len(self.post_select) > 0:
            raise NotImplementedError()
        return self.do_sample(n_shot)

    def do_sample(self, n_shot):
        qc, q = self._build_circuit()
        qc.measure(self._all_register(), self._all_register())

        def listener(result):
            samples = []
            for bitstring, count in result.get_counts().items():
                for i in range(count):
                    bitarray = self.encoder.to_bitarray(bitstring)
                    samples.append(Sample(bitarray))
            random.shuffle(samples)
            return samples

        job = qiskit.execute(qc, self.simulator, shots=n_shot,
                             initial_layout=self.circuit.layout)
        future = SampleJobFuture(job, listener)
        return future

    def exact_probabilities(self):
        results = {}
        partial_qubits = self.n_qubit - len(self.post_select)
        partial_encoder = Encoder(partial_qubits)
        valid = False
        while not valid:
            statevector = self.get_state_vector()
            valid = True
            for num, c in enumerate(statevector):
                bit_array = self.encoder.encode(num)
                for k, v in sorted(self.post_select.items(), key=lambda a: a[0], reverse=True):
                    if bit_array.pop(self.n_qubit - k - 1) != v and abs(c * c.conjugate()) > 0:
                        valid = False
                if not valid:
                    continue
                key = partial_encoder.decode(bit_array)
                results[key] = abs(c * c.conjugate())
        rs = []
        for _, p in sorted(results.items(), key=lambda a: a[0]):
            rs.append(p)
        return rs

    def get_state_vector(self):
        qc, q = self._build_circuit()
        job = qiskit.execute(qc, self.state_simulator)
        statevector = job.result().get_statevector(qc)
        return statevector

    def add_post_select(self, qubit_index, qubit_value):
        self.post_select[qubit_index] = qubit_value

    def _all_register(self):
        r = []
        for i in range(self.n_qubit):
            r.append(i)
        return r

    def _build_circuit(self):
        q = qiskit.QuantumRegister(self.n_qubit)
        qc = qiskit.QuantumCircuit(q, qiskit.ClassicalRegister(self.n_qubit))
        qc, q_register = self.circuit.merge(qc, q)
        return qc, q


class Parametrized(Sampler):
    def get_parameters(self):
        return []

    def copy(self, parameters):
        pass


class ParametrizedQiskitSampler(Parametrized, QiskitSampler):
    def __init__(self, circuit: RandomCircuit, n_qubit):
        super().__init__(circuit, n_qubit)
        self.circuit = circuit

    def get_parameters(self):
        return self.circuit.parameters

    def copy(self, parameters):
        self.circuit.copy(parameters)

    def name(self):
        return "ParametrizedQiskitSampler"


class ParametrizedQiskitSamplerFactory:
    def __init__(self, layer_count, n_qubit):
        self.layer_count = layer_count
        self.n_qubit = n_qubit

    def plus_sampler(self, sampler: ParametrizedQiskitSampler, index):
        circuit = plus_circuit(sampler.circuit, index)
        return ParametrizedQiskitSampler(circuit, circuit.n_qubit)

    def minus_sampler(self, sampler: ParametrizedQiskitSampler, index):
        circuit = minus_circuit(sampler.circuit, index)
        return ParametrizedQiskitSampler(circuit, circuit.n_qubit)

    def generate_he(self):
        circuit = HECircuitFactory.generate(self.layer_count, self.n_qubit)
        return self._create_instance(circuit)

    def generate_real_he(self):
        circuit = HECircuitFactory.generate_real(self.layer_count, self.n_qubit)
        return self._create_instance(circuit)

    def generate_ten(self, n_a, n_b):
        circuit = TENCircuitFactory.generate(self.layer_count, self.n_qubit, n_a, n_b)
        return self._create_instance(circuit)

    def save(self, filename, sampler: ParametrizedQiskitSampler, extra: {}):
        with open(filename, "w") as f:
            directions = []
            parameters = []
            for i, p in enumerate(sampler.circuit.parameters):
                directions.append(sampler.circuit.directions[i])
                parameters.append(p)
            result = {"name": sampler.name(),
                      "directions": directions,
                      "parameters": parameters,
                      "extra": extra,
                      "n_qubit": self.n_qubit}
            f.write(json.dumps(result, indent=2))

    def load(self, filename):
        with open(filename) as f:
            map = json.loads(f.read())
            directions = map["directions"]
            parameters = map["parameters"]
            n_qubit = map["n_qubit"]
            circuit = HECircuitFactory.do_generate(parameters, directions, n_qubit)
            return self._create_instance(circuit)

    def create_instance(self, circuit):
        return ParametrizedQiskitSampler(circuit, self.n_qubit)

    def _create_instance(self, circuit):
        return ParametrizedQiskitSampler(circuit, self.n_qubit)


class Converter:
    def convert(self, sampler: Sampler):
        return sampler

    def revoke(self, sampler: Sampler):
        return sampler


class CircuitAppender(Converter):
    def __init__(self, circuit: QiskitCircuit):
        self.circuit = circuit

    def convert(self, sampler: ParametrizedQiskitSampler):
        sampler.circuit.additional_circuit = self.circuit
        return sampler

    def revoke(self, sampler: Sampler):
        sampler.circuit.additional_circuit = None
