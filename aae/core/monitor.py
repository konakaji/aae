from matplotlib import pyplot as plt

from aae.core.entity import Probability
from aae.core.exact_cost import Cost
from aae.core.sampler import Converter, Sampler


class ImageGenrator:
    def __init__(self, output_directory, probability: Probability, converter: Converter = None):
        self.output = output_directory
        self.probability = probability
        self.converter = converter
        self.probability_title = None
        self.state_title = None
        self.plt_option_func = None

    def generate(self, step, sampler):
        plt.clf()
        if self.plt_option_func is not None:
            self.plt_option_func(plt)
        if self.converter is not None:
            sampler = self.converter.convert(sampler)
        self.probability.plot(self.probability_title)
        self.probability.plot_state(sampler.exact_probabilities(), self.state_title)
        plt.legend(fontsize="12")
        plt.savefig(self.output + "/" + str(step) + ".png")
        if self.converter is not None:
            self.converter.revoke(sampler)


class TaskWatcher:
    def __init__(self, image_generators: [ImageGenrator], costs=[Cost]):
        self.costs = costs
        self.image_generators = image_generators
        self.step = 0
        self.records = []

    def record(self, sampler: Sampler):
        for cost in self.costs:
            sampler.circuit.additional_circuit = None
            print(self.step, cost.name(), cost.value(sampler))
            self.records.append((self.step, cost.name(), cost.value(sampler)))
        if self.step % 10 == 0:
            sampler.circuit.additional_circuit = None
            for image_generator in self.image_generators:
                image_generator.generate(self.step, sampler)
        self.step = self.step + 1

    def save_energy(self, path):
        with open(path, "w") as o:
            for record in self.records:
                o.write("{}\t{}\t{}\n".format(record[0], record[1], record[2]))
