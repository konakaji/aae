import sys, warnings
import qiskit

sys.path.append("../")
warnings.filterwarnings('ignore')

from svd.extention.data_learning import DataLearning

DEMO_FILENAME = "demo"
N_SHOT = 200


def load():
    data_learning = DataLearning(n_qubit=3, layer=4)
    data_learning.load(DEMO_FILENAME)
    qr = qiskit.QuantumRegister(3)
    cr = qiskit.ClassicalRegister(3)
    qc = qiskit.QuantumCircuit(qr, cr)
    data_learning.add_data_gates(qc, qr)
    # add gates for quantum algorithm-------
    #---------------------------------------
    qc.measure(1, 1)
    qc.measure(2, 2)
    simulator = qiskit.Aer.get_backend("qasm_simulator")
    print(data_learning.get_state_vector())
    future = data_learning.execute_with_post_selection(qc, simulator, shots=N_SHOT)
    samples = future.get()
    for sample in samples:
        print(sample)


def learn():
    data_learning = DataLearning(n_qubit=3, layer=4)
    data_learning.learn([0, 0, 1, 0], n_shot=N_SHOT, filename=DEMO_FILENAME, iteration=30)


if __name__ == '__main__':
    learn()
    load()
