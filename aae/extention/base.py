from abc import ABC, abstractmethod
from aae.core.task import GradientOptimizationTask
from qiskit import QuantumCircuit, QuantumRegister


class TrainingMethod(ABC):
    def __init__(self):
        self.task_watcher = None

    @abstractmethod
    def build(self, data_sampler, coefficients, n_qubit, factory) -> GradientOptimizationTask:
        pass

    @abstractmethod
    def get_cost(self, data_sampler):
        pass

    @classmethod
    def get_name(cls):
        pass


class LoadingMethod(ABC):
    @abstractmethod
    def add_data_gates(self, sampler, q_circuit: QuantumCircuit, q_register: QuantumRegister):
        pass

    @abstractmethod
    def get_state_vector(self, sampler):
        pass


class DefaultLoadingMethod(LoadingMethod):
    def add_data_gates(self, sampler, q_circuit: QuantumCircuit, q_register: QuantumRegister):
        c, q_register = sampler.circuit.merge(q_circuit, q_register)
        return c

    def get_state_vector(self, sampler):
        return sampler.get_state_vector()
