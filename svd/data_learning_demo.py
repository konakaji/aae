import sys, warnings, math
from svd.core.encoder import Encoder
import qiskit

sys.path.append("../")
warnings.filterwarnings('ignore')

from svd.extention.data_learning import DataLearning, PositiveDataLearning

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
    # qc.xxx()
    # ---------------------------------------
    qc.measure(1, 1)
    qc.measure(2, 2)
    simulator = qiskit.Aer.get_backend("qasm_simulator")
    future = data_learning.execute_with_post_selection(qc, simulator, shots=N_SHOT)
    samples = future.get()
    for sample in samples:
        print(sample)


def learn():
    data_learning = DataLearning(n_qubit=3, layer=4)
    data_learning.learn([0, 0, 1, 0], n_shot=N_SHOT, filename=DEMO_FILENAME, iteration=30)
    print(data_learning.get_state_vector())


def get_count(job_result):
    return job_result.get_counts().items()


def load_positive():
    n_qubit = 3
    n_shot = 8024
    data_learning = PositiveDataLearning(n_qubit=n_qubit, layer=2)
    data_learning.load("simulator", device="ibmq_rome")
    data_learning.get_samples(8024).get()
    values = normalize([0.1, 0.3, 0.4, 0.2, 0.4, 0.5, 0.3, 0.2])
    future = data_learning.get_samples(8024)
    future.listener = get_count
    vector = [0] * pow(2, n_qubit)
    encoder = Encoder(n_qubit)
    for bit_string, count in future.get():
        index = int(encoder.decode(encoder.to_bitarray(bit_string)))
        vector[index] = math.sqrt(count / n_shot)
    print(fidelity(values, vector))


def learn_positive():
    n_qubit = 3
    data_learning = PositiveDataLearning(n_qubit=n_qubit, layer=2)
    encoder = Encoder(n_qubit)
    n_shot = 8024
    values = normalize([0.1, 0.3, 0.4, 0.2, 0.4, 0.5, 0.3, 0.2])
    # values = normalize([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    data_learning.load("simulator")
    data_learning.learn(values, device="ibmq_rome", n_shot=N_SHOT, filename="rome", iteration=5)


#    data_learning.learn(values, n_shot=N_SHOT, filename="simulator", iteration=50)
# future = data_learning.get_samples(n_shot)
# future.listener = get_count
# vector = [0] * pow(2, n_qubit)
# for bit_string, count in future.get():
#     index = int(encoder.decode(encoder.to_bitarray(bit_string)))
#     vector[index] = math.sqrt(count / n_shot)
# print(fidelity(values, data_learning.get_state_vector()))
# print(fidelity(values, vector))
# print(fidelity(vector, data_learning.get_state_vector()))


def fidelity(values, state_vector):
    print(values)
    print(state_vector)
    result = 0
    for i, v in enumerate(values):
        result = result + state_vector[i] * v
    return result * result


def normalize(state_array):
    norm = 0
    for v in state_array:
        norm = norm + v * v
    return [v / math.sqrt(norm) for v in state_array]


if __name__ == '__main__':
#    learn_positive()
    load_positive()
    # learn()
    # load()
