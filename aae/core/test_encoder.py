from unittest import TestCase
from aae.core.encoder import Encoder
import numpy as np
from qiskit.circuit import QuantumCircuit
import qiskit

class TestEncoder(TestCase):
    def test_encode(self):
        encoder = Encoder(2)
        array = encoder.encode(2)
        np.testing.assert_array_equal(array, [1, 0])
        array = encoder.encode(3)
        np.testing.assert_array_equal(array, [1, 1])

    def test_decode(self):
        encoder = Encoder(2)
        v = encoder.decode([0, 1])
        self.assertEqual(1, v)

    def test_consistent_with_qiskit(self):
        qc = QuantumCircuit(2)
        qc.x(0)
        simulator = qiskit.Aer.get_backend("statevector_simulator")
        encoder = Encoder(2)
        job = qiskit.execute(qc, simulator)
        # |01>
        statevector = job.result().get_statevector(qc)
        for num, s in enumerate(statevector):
            bit_array = encoder.encode(num)
            if bit_array[0] == 0 and bit_array[1] == 1:
                self.assertEqual(s, 1)
            else:
                self.assertEqual(s, 0)
        # namely, the zero-th qubit of the qiskit coressponds to the 0-th bit array