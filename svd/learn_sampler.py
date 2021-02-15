import math, sys, warnings, random
from time import time

sys.path.append("../")
warnings.filterwarnings('ignore')
from svd.core.sampler import ParametrizedQiskitSamplerFactory, Sampler
from svd.core.sampler import Converter, ParametrizedQiskitSampler
from svd.core.task import AdamGradientOptimizationTask
from svd.core.gradient_cost import MultipleMMDGradientCost, MMDGradientCost
from svd.core.exact_cost import KLCost, MMDCost
from svd.core.util import TaskWatcher, ImageGenrator
from svd.core.optimizer import AdamOptimizer, TransformingLRScheduler
from svd.core.encoder import Encoder
from svd.core.circuit import AllHadamardCircuit, QiskitCircuit
from svd.finance.context import Context
import svd.constant as const
from argparse import ArgumentParser


class CircuitAppender(Converter):
    def __init__(self, circuit: QiskitCircuit):
        self.circuit = circuit

    def convert(self, sampler: ParametrizedQiskitSampler):
        sampler.circuit.additional_circuit = self.circuit
        return sampler

    def revoke(self, sampler: Sampler):
        sampler.circuit.additional_circuit = None


def gaussian_kernel(variance):
    def result(x, y):
        return math.exp(-pow(x - y, 2) / variance)

    return result


def build_gradient_cost(args, probability, another_probability, additional_circuit, encoder):
    mmd_gradient_cost = MultipleMMDGradientCost(probability, another_probability,
                                                additional_circuit, encoder,
                                                lambda_1=0.5, lambda_2=0.5)
    mmd_gradient_cost.custom_kernel = gaussian_kernel(args.variance)
    mmd_gradient_cost.cutoff = args.cutoff
    return mmd_gradient_cost


def build_naive_gradient_cost(args, probability, encoder):
    mmd_gradient_cost = MMDGradientCost(probability, encoder)
    mmd_gradient_cost.custom_kernel = gaussian_kernel(args.variance)
    mmd_gradient_cost.cutoff = args.cutoff
    return mmd_gradient_cost


def build_naive_task(args, probability, encoder, data_sampler, factory, optimizer):
    mmd_gradient_cost = build_naive_gradient_cost(args, probability, encoder)
    kl_cost = KLCost(probability, encoder)
    mmd_cost = MMDCost(probability, encoder)
    mmd_cost.custom_kernel = gaussian_kernel(args.variance)
    task_watcher = TaskWatcher([ImageGenrator(const.OPTIMIZATION_FIGURE_PATH, probability)],
                               [kl_cost, mmd_cost])

    def total_cost(sampler):
        return mmd_cost.value(sampler)

    return AdamGradientOptimizationTask(data_sampler, factory, mmd_gradient_cost,
                                        task_watcher, args.nshot, optimizer), total_cost


def build_task(args, probability, another_probability, additional_circuit, encoder,
               converter, data_sampler, factory, optimizer):
    mmd_gradient_cost = build_gradient_cost(args, probability, another_probability, additional_circuit, encoder)
    # costs used just for displaying (computed by using state_vector)
    kl_cost = KLCost(probability, encoder)
    another_kl_cost = KLCost(another_probability, encoder, converter)
    mmd_cost = MMDCost(probability, encoder)
    mmd_cost.custom_kernel = gaussian_kernel(args.variance)
    another_mmd_cost = MMDCost(another_probability, encoder, CircuitAppender(additional_circuit))
    task_watcher = TaskWatcher([ImageGenrator(const.OPTIMIZATION_FIGURE_PATH, probability),
                                ImageGenrator(const.SECOND_OPTIMIZATION_FIGURE_PATH, another_probability,
                                              converter=converter)],
                               [kl_cost, another_kl_cost, mmd_cost, another_mmd_cost])

    def total_cost(sampler):
        return mmd_cost.value(sampler) + another_mmd_cost.value(data_sampler)

    return AdamGradientOptimizationTask(data_sampler, factory, mmd_gradient_cost,
                                        task_watcher, args.nshot, optimizer), total_cost


def do_learn(args, output, energy_output, coefficient, naive=False):
    probability = coefficient.to_probability()
    another_probability = coefficient.to_hadamard_probability()
    if naive:
        probability = coefficient.to_naive_probability()
    encoder = Encoder(probability.N)
    n_qubit = probability.N
    factory = ParametrizedQiskitSamplerFactory(args.layer, n_qubit)
    data_sampler = factory.generate_real_he()
    data_sampler.encoder = encoder
    if args.device is not None:
        from ibmq.base import get_backend, DeviceFactory
        device_factory = DeviceFactory(args.device, reservation=args.reservation)
        data_sampler.simulator = device_factory.get_backend()
        data_sampler.factory = device_factory
    scheduler = TransformingLRScheduler(lr=args.lr)
    scheduler.schedule(100, 0.01)
    optimizer = AdamOptimizer(scheduler, maxiter=args.iter)
    additional_circuit = AllHadamardCircuit(n_qubit)
    converter = CircuitAppender(additional_circuit)
    # cost used for optimization (computed by sampling)
    if not naive:
        optimization, total_cost = build_task(args, probability, another_probability, additional_circuit, encoder,
                                              converter, data_sampler,
                                              factory,
                                              optimizer)
    else:
        optimization, total_cost = build_naive_task(args, probability, encoder, data_sampler, factory, optimizer)
    # module to print the progress
    # the main optimization algorithm
    optimization.optimize()
    # save the progress to the file
    optimization.task_watcher.save(energy_output)
    # save the model to the file
    factory.save(output, data_sampler,
                 {const.ENERGY_KEY: total_cost(data_sampler) + total_cost(data_sampler),
                  const.LAYER_KEY: args.layer})
    return data_sampler


def learn(args):
    context = Context()
    usecase = context.get_coefficient_usecase()
    for i in range(args.trial):
        for date_index in range(args.ds, args.de + 1):
            random.seed(31 * i + 17 * date_index)
            coefficient = usecase.load(const.TIME_SPAN, date_index, sub=const.STOCK_COUNT)
            label = int(time())
            filename = "{}/{}-{}-{}.txt".format(const.MODEL_PATH, args.prefix, date_index, label)
            energy_filename = "{}/{}-{}-{}.txt".format(const.ENERGY_PATH, args.prefix, date_index, label)
            sampler = do_learn(args, filename, energy_filename, coefficient,
                               args.prefix == const.NAIVE_PREFIX)
            sampler.circuit.another_circuit = None


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-d", "--device", help='name of the ibmq device ex: ibmq_tronto')
    parser.add_argument("-i", "--iter", help='# of iterations in a trial', type=int, default=200)
    parser.add_argument("-r", "--reservation", type=bool, help='if you made reservation, set true', default=False)
    parser.add_argument("-t", "--trial", help='# of trials', type=int, default=10)
    parser.add_argument("-l", "--layer", help='# of layers', type=int, default=6)
    parser.add_argument("-n", "--nshot", help='# of Nshot', type=int, default=400)
    parser.add_argument("-v", "--variance", help='variance of Gaussian Kernel', type=float, default=0.25)
    parser.add_argument("-ds", help='start of date index', type=int, default=0)
    parser.add_argument("-de", help='end of date index', type=int, default=7)
    parser.add_argument("-c", "--cutoff", help='cut off of the kernel', type=int, default=1)
    parser.add_argument("--prefix", help='pr1efix of the model and the energy files', default=const.DEFAULT_PREFIX)
    parser.add_argument("-lr", help='learning rate', type=int, default=0.1)
    args = parser.parse_args()
    print(args)
    learn(args)
