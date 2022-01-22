import qiskit, random, math
from aae.core.exception import *
from qwrapper.circuit import QWrapper as QuantumCircuit, QiskitCircuit, QulacsCircuit

QISKIT = "qiskit"
QULACS = "qulacs"


class Gates:
    def __init__(self, n_qubit):
        self.n_qubit = n_qubit
        self.layout = qiskit.transpiler.Layout.generate_trivial_layout()

    def merge(self, circuit: QuantumCircuit):
        return circuit

    def to_circuit(self, type=QISKIT) -> QuantumCircuit:
        if type == QISKIT:
            qc = QiskitCircuit(self.n_qubit)
        elif type == QULACS:
            qc = QulacsCircuit(self.n_qubit)
        else:
            raise IllegalArgumentException("type not found {}".format(type))
        return self.merge(qc)

    def dagger(self):
        return None


class Hadamard(Gates):
    def __init__(self, target):
        self.target = target
        # super().__init__(n_qubit)

    def merge(self, circuit: QuantumCircuit):
        circuit.h(self.target)
        circuit.barrier()
        return circuit


class AllHadamardGates(Gates):
    def __init__(self, n_qubit):
        super().__init__(n_qubit)

    def merge(self, circuit: QuantumCircuit):
        for i in range(self.n_qubit):
            circuit.h(i)
        return circuit


class RandomGates(Gates):
    def __init__(self, parameters, directions, n_qubit, opposite_ladder=False):
        super().__init__(n_qubit)
        self.parameters = parameters
        self.directions = directions
        self.opposite_ladder = opposite_ladder
        self.additional_circuit = None
        self.draw_mode = False
        self.parameter_name = "\\theta"

    def copy(self, parameters):
        self.parameters = parameters

    def merge(self, circuit: QuantumCircuit):
        for i, parameter in enumerate(self.parameters):
            if self.opposite_ladder:
                target_qubit = self.n_qubit - i % self.n_qubit - 1
                if target_qubit == self.n_qubit - 1:
                    self.add_ladder_for_odd(circuit)
                    self.add_ladder_for_even(circuit)
                    circuit.barrier()
                self._single_gate(self.directions[i], parameter, target_qubit, circuit, i)
            else:
                target_qubit = i % self.n_qubit
                self._single_gate(self.directions[i], parameter, target_qubit, circuit, i)
                if target_qubit == self.n_qubit - 1:
                    self.add_ladder_for_even(circuit)
                    self.add_ladder_for_odd(circuit)
                    circuit.barrier()
        if self.additional_circuit is not None:
            circuit = self.additional_circuit.merge(circuit)
        return circuit

    def add_ladder_for_odd(self, circuit: QuantumCircuit):
        pass

    def add_ladder_for_even(self, circuit: QuantumCircuit):
        pass

    def is_single_rotation_target(self, target_qubit):
        return True

    def _single_gate(self, direction, parameter, target_qubit, qc: QuantumCircuit, index):
        if not self.is_single_rotation_target(target_qubit):
            return
        if self.draw_mode:
            self._single_draw_gate(direction, target_qubit, qc, index)
            return
        if direction == 0:
            qc.rx(parameter, target_qubit)
        elif direction == 1:
            qc.ry(parameter, target_qubit)
        elif direction == 2:
            qc.rz(parameter, target_qubit)

    def _single_draw_gate(self, direction, target_qubit, qc: QuantumCircuit, index):
        q_register = qc.get_q_register()
        if not isinstance(qc, QiskitCircuit):
            raise IllegalArgumentException("draw function is not implemented in this type of the circuit")
        directions = ["x", "y", "z"]
        qc.qc.append(qiskit.circuit.Gate(name=r'$R_' + directions[direction]
                                              + '(' + self.parameter_name + '_{' + str(index + 1) + '})$',
                                         num_qubits=1, params=[]), [q_register[target_qubit]])


class HECircuit(RandomGates):
    def __init__(self, parameters, directions, n_qubit, opposite_ladder=False):
        super().__init__(parameters, directions, n_qubit, opposite_ladder)

    def add_ladder_for_odd(self, circuit: QuantumCircuit):
        j = 0
        while 2 * j + 1 < self.n_qubit - 1:
            circuit.cx(2 * j + 1, 2 * j + 2)
            j = j + 1

    def add_ladder_for_even(self, circuit: QuantumCircuit):
        j = 0
        while 2 * j < self.n_qubit - 1:
            circuit.cx(2 * j, 2 * j + 1)
            j = j + 1

    def dagger(self):
        parameters = []
        directions = []
        n = len(self.parameters)
        for i in range(n):
            k = n - 1 - i
            parameters.append(-self.parameters[k])
            directions.append(self.directions[k])
        return HECircuit(parameters, directions, self.n_qubit, True)


class TENCircuit(RandomGates):
    def __init__(self, parameters, directions, n_qubit, n_a, n_b, opposite_ladder=False):
        super().__init__(parameters, directions, n_qubit, opposite_ladder)
        self.n_a = n_a
        self.n_b = n_b
        self.another_parameter_name = "\\theta"

    def add_ladder_for_odd(self, circuit: QuantumCircuit):
        offset = self.n_qubit - self.n_a - self.n_b
        j = math.ceil((offset - 1) / 2)
        while 2 * j + 1 < self.n_qubit - 1:
            if 2 * j + 1 == offset + self.n_a - 1:
                j = j + 1
                continue
            circuit.cx(2 * j + 1, 2 * j + 2)
            j = j + 1

    def add_ladder_for_even(self, circuit: QuantumCircuit):
        offset = self.n_qubit - self.n_a - self.n_b
        j = math.ceil(offset / 2)
        while 2 * j < self.n_qubit - 1:
            if 2 * j == offset + self.n_a - 1:
                j = j + 1
                continue
            circuit.cx(2 * j, 2 * j + 1)
            j = j + 1

    def is_single_rotation_target(self, target_qubit):
        return target_qubit >= self.n_qubit - self.n_a - self.n_b

    def dagger(self):
        parameters = []
        directions = []
        n = len(self.parameters)
        for i in range(n):
            k = n - 1 - i
            parameters.append(-self.parameters[k])
            directions.append(self.directions[k])
        return TENCircuit(parameters, directions, self.n_qubit, self.n_a, self.n_b, True)

    def _single_draw_gate(self, direction, target_qubit, qc: QuantumCircuit, index):
        q_register = qc.get_q_register()
        if not isinstance(qc, QiskitCircuit):
            raise IllegalArgumentException("draw function is not implemented in this type of the circuit")
        offset = self.n_qubit - self.n_a - self.n_b
        layer = math.ceil(index / self.n_qubit)
        position = index % self.n_qubit
        if 0 <= position < offset:
            return
        elif offset <= position < offset + self.n_a:
            index = self.n_a * layer + position - offset
            name = self.parameter_name
        else:
            index = layer * self.n_b + position - (offset + self.n_a)
            name = self.another_parameter_name
        directions = ["x", "y", "z"]
        qc.qc.append(qiskit.circuit.Gate(name=r'$R_' + directions[direction]
                                              + '(' + name + '_{' + str(index + 1) + '})$',
                                         num_qubits=1, params=[]), [q_register[target_qubit]])


class CompositeRandomGates(Gates):
    def __init__(self, circuits: [Gates]):
        super().__init__(circuits[0].n_qubit)
        self.circuits = circuits

    def merge(self, circuit: Gates):
        for c in self.circuits:
            circuit = c.merge(circuit)
        return circuit

    def dagger(self):
        count = len(self.circuits)
        circuits = []
        for i in range(count):
            index = count - i - 1
            c = self.circuits[index].dagger()
            circuits.append(c)
        return CompositeRandomGates(circuits)


class TENCircuitFactory:
    @classmethod
    def generate(cls, layer_count, n_qubit, na, nb):
        parameters = []
        directions = []
        dimension = layer_count * n_qubit
        for i in range(dimension):
            parameters.append(random.uniform(0, math.pi * 2))
            directions.append(random.randint(0, 2))
        return cls.do_generate(parameters, directions, n_qubit, na, nb)

    @classmethod
    def do_generate(cls, parameters, directions, n_qubit, na, nb):
        return TENCircuit(parameters, directions, n_qubit, na, nb)


class HECircuitFactory:
    @classmethod
    def generate(cls, layer_count, n_qubit):
        parameters = []
        directions = []
        dimension = layer_count * n_qubit
        for i in range(dimension):
            parameters.append(random.uniform(0, math.pi * 2))
            directions.append(random.randint(0, 2))
        return cls.do_generate(parameters, directions, n_qubit)

    @classmethod
    def generate_real(cls, layer_count, n_qubit):
        parameters = []
        directions = []
        dimension = layer_count * n_qubit
        for i in range(dimension):
            parameters.append(random.uniform(0, math.pi * 2))
            directions.append(1)
        return cls.do_generate(parameters, directions, n_qubit)

    @classmethod
    def do_generate(cls, parameters, directions, n_qubit):
        return HECircuit(parameters, directions, n_qubit)

    @classmethod
    def override(cls, circuit: HECircuit, parameters):
        return HECircuit(parameters, circuit.directions, circuit.n_qubit)


def plus_circuit(circuit: HECircuit, index):
    return override_circuit(circuit, index, math.pi / 2)


def minus_circuit(circuit: HECircuit, index):
    return override_circuit(circuit, index, -math.pi / 2)


def override_circuit(circuit: HECircuit, index, plus):
    params = []
    for i, p in enumerate(circuit.parameters):
        if index == i:
            params.append(p + plus)
        else:
            params.append(p)
    return HECircuitFactory.override(circuit, params)
