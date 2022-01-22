import math
import qiskit
from aae.extention.data_learning import DataLearning
from aae.extention.aae import AAETrainingMethod, PositiveAAETrainingMethod, AAEUtil

DEMO_FILENAME = "demo"
N_SHOT = 200


def load():
    print("----load----")
    data_learning = DataLearning(n_qubit=3, layer=4)
    data_learning.load("demo.model")
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
    future = AAEUtil.execute_with_post_selection(qc, simulator, shots=N_SHOT, n=3)
    samples = future.get()


def learn():
    print("----learn----")
    data_learning = DataLearning(n_qubit=3, layer=4, type="qulacs")
    training_method = AAETrainingMethod(iteration=20)
    result = data_learning.learn([0, 0, 1, 0], training_method=training_method)
    print(data_learning.get_state_vector())
    data_learning.save_model("demo.model")
    data_learning.save_cost_transition("cost.txt")


def get_count(job_result):
    return job_result.get_counts().items()


def load_positive():
    print("----load positive----")
    n_qubit = 3
    data_learning = DataLearning(n_qubit=n_qubit, layer=2)
    data_learning.load("positive.model")
    print(data_learning.get_state_vector())


def learn_positive():
    print("----learn positive----")
    n_qubit = 3
    training_method = PositiveAAETrainingMethod(iteration=20)
    data_learning = DataLearning(n_qubit=n_qubit, layer=2)
    result = data_learning.learn(normalize([0.1, 0.3, 0.4, 0.2, 0.4, 0.5, 0.3, 0.2]), training_method=training_method)
    print(result)
    data_learning.save_model("positive.model")
    data_learning.save_cost_transition("positive.txt")


def normalize(state_array):
    norm = 0
    for v in state_array:
        norm = norm + v * v
    return [v / math.sqrt(norm) for v in state_array]


if __name__ == '__main__':
    learn()
    # load()
    # learn_positive()
    # load_positive()
