from aae.core.optimizer import AdamOptimizer
from aae.core.sampler import Parametrized, ParametrizedQiskitSampler, ParametrizedQiskitSamplerFactory
from aae.core.gradient_cost import GradientCost
from aae.core.exact_cost import Cost
from aae.core.util import TaskWatcher


class AdamOptimizationTask:
    def __init__(self, sampler: Parametrized,
                 cost: Cost, optimizer: AdamOptimizer):
        self.sampler = sampler
        self.cost = cost
        self.optimizer = optimizer
        self.function = self.build_function()
        self.iteration = 0

    def build_function(self):
        sampler = self.sampler

        def function(parameters):
            sampler.copy(parameters)
            c = self.cost.value(sampler)
            self.iteration = self.iteration + 1
            return c

        return function

    def optimize(self):
        parameters = self.sampler.get_parameters()
        self.optimizer.optimize(self.function, parameters)


class AdamGradientOptimizationTask:
    def __init__(self, sampler: ParametrizedQiskitSampler,
                 factory: ParametrizedQiskitSamplerFactory,
                 cost: GradientCost, task_watcher: TaskWatcher, n_shot, optimizer: AdamOptimizer):
        self.sampler = sampler
        self.factory = factory
        self.cost = cost
        self.task_watcher = task_watcher
        self.n_shot = n_shot
        self.optimizer = optimizer
        self.gradient_function = self.build_gradient_function()

    def build_gradient_function(self):
        sampler = self.sampler
        factory = self.factory
        n_shot = self.n_shot

        def function(parameters):
            self.task_watcher.record(sampler)
            sampler.copy(parameters)
            return self.cost.sample_gradient(sampler, factory, n_shot)

        return function

    def optimize(self):
        self.step = 0
        parameters = self.sampler.get_parameters()
        self.optimizer.do_optimize(self.gradient_function, parameters)