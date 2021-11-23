import qiskit, random, math


class QiskitCircuit:
    def __init__(self, n_qubit):
        self.n_qubit = n_qubit
        self.layout = qiskit.transpiler.Layout.generate_trivial_layout()

    def merge(self, circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        return circuit, q_register

    def to_qiskit(self):
        q = qiskit.QuantumRegister(self.n_qubit)
        qc = qiskit.QuantumCircuit(q, qiskit.ClassicalRegister(self.n_qubit))
        return self.merge(qc, q)[0]

    def dagger(self):
        return None


class HadamardAndMeausre(QiskitCircuit):
    def __init__(self, target):
        self.target = target

    def merge(self, circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        circuit.h(self.target)
        circuit.measure([self.target], [self.target])
        circuit.barrier()
        return circuit, q_register


class AllHadamardCircuit(QiskitCircuit):
    def __init__(self, n_qubit):
        super().__init__(n_qubit)

    def merge(self, circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        for i in range(self.n_qubit):
            circuit.h(i)
        return circuit, q_register


class RandomCircuit(QiskitCircuit):
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

    def merge(self, circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        for i, parameter in enumerate(self.parameters):
            if self.opposite_ladder:
                target_qubit = self.n_qubit - i % self.n_qubit - 1
                if target_qubit == self.n_qubit - 1:
                    self.add_ladder_for_odd(circuit)
                    self.add_ladder_for_even(circuit)
                    circuit.barrier()
                self._single_gate(self.directions[i], parameter, target_qubit, circuit, q_register, i)
            else:
                target_qubit = i % self.n_qubit
                self._single_gate(self.directions[i], parameter, target_qubit, circuit, q_register, i)
                if target_qubit == self.n_qubit - 1:
                    self.add_ladder_for_even(circuit)
                    self.add_ladder_for_odd(circuit)
                    circuit.barrier()
        if self.additional_circuit is not None:
            circuit, q_register = self.additional_circuit.merge(circuit, q_register)
        return circuit, q_register

    def add_ladder_for_odd(self, circuit: qiskit.QuantumCircuit):
        pass

    def add_ladder_for_even(self, circuit: qiskit.QuantumCircuit):
        pass

    def is_single_rotation_target(self, target_qubit):
        return True

    def _single_gate(self, direction, parameter, target_qubit, qc: qiskit.QuantumCircuit,
                     q_register: qiskit.QuantumRegister, index):
        if not self.is_single_rotation_target(target_qubit):
            return
        if self.draw_mode:
            self._single_draw_gate(direction, target_qubit, qc, q_register, index)
            return
        if direction == 0:
            qc.rx(parameter, target_qubit)
        elif direction == 1:
            qc.ry(parameter, target_qubit)
        elif direction == 2:
            qc.rz(parameter, target_qubit)

    def _single_draw_gate(self, direction, target_qubit, qc: qiskit.QuantumCircuit,
                          q_register: qiskit.QuantumRegister, index):
        directions = ["x", "y", "z"]
        qc.append(qiskit.circuit.Gate(name=r'$R_' + directions[direction]
                                           + '(' + self.parameter_name + '_{' + str(index + 1) + '})$',
                                      num_qubits=1, params=[]), [q_register[target_qubit]])



class HECircuit(RandomCircuit):
    def __init__(self, parameters, directions, n_qubit, opposite_ladder=False):
        super().__init__(parameters, directions, n_qubit, opposite_ladder)

    def add_ladder_for_odd(self, circuit: qiskit.QuantumCircuit):
        j = 0
        while 2 * j + 1 < self.n_qubit - 1:
            circuit.cx(2 * j + 1, 2 * j + 2)
            j = j + 1

    def add_ladder_for_even(self, circuit: qiskit.QuantumCircuit):
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


class TENCircuit(RandomCircuit):
    def __init__(self, parameters, directions, n_qubit, n_a, n_b, opposite_ladder=False):
        super().__init__(parameters, directions, n_qubit, opposite_ladder)
        self.n_a = n_a
        self.n_b = n_b
        self.another_parameter_name = "\\theta"

    def add_ladder_for_odd(self, circuit: qiskit.QuantumCircuit):
        offset = self.n_qubit - self.n_a - self.n_b
        j = math.ceil((offset - 1) / 2)
        while 2 * j + 1 < self.n_qubit - 1:
            if 2 * j + 1 == offset + self.n_a - 1:
                j = j + 1
                continue
            circuit.cx(2 * j + 1, 2 * j + 2)
            j = j + 1

    def add_ladder_for_even(self, circuit: qiskit.QuantumCircuit):
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

    def _single_draw_gate(self, direction, target_qubit, qc: qiskit.QuantumCircuit,
                          q_register: qiskit.QuantumRegister, index):
        offset = self.n_qubit - self.n_a - self.n_b
        layer = math.ceil(index / self.n_qubit)
        position = index % self.n_qubit
        name = None
        if 0 <= position < offset:
            return
        elif offset <= position < offset + self.n_a:
            index = self.n_a * layer + position - offset
            name = self.parameter_name
        else:
            index = layer * self.n_b + position - (offset + self.n_a)
            name = self.another_parameter_name
        directions = ["x", "y", "z"]
        qc.append(qiskit.circuit.Gate(name=r'$R_' + directions[direction]
                                           + '(' + name + '_{' + str(index + 1) + '})$',
                                      num_qubits=1, params=[]), [q_register[target_qubit]])


class CompositeRandomCircuit(QiskitCircuit):
    def __init__(self, circuits: [QiskitCircuit]):
        super().__init__(circuits[0].n_qubit)
        self.circuits = circuits

    def merge(self, circuit: QiskitCircuit, q_register: qiskit.QuantumRegister):
        for c in self.circuits:
            circuit, q_register = c.merge(circuit, q_register)
        return circuit, q_register

    def dagger(self):
        count = len(self.circuits)
        circuits = []
        for i in range(count):
            index = count - i - 1
            c = self.circuits[index].dagger()
            circuits.append(c)
        return CompositeRandomCircuit(circuits)


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


def copy_random_circuit(circuit: RandomCircuit, n_qubit) -> QiskitCircuit:
    q = qiskit.QuantumRegister(n_qubit)
    c = qiskit.QuantumCircuit(q)
    return circuit.merge(c, q)
