import sys, warnings

sys.path.append("../")
warnings.filterwarnings('ignore')

from svd.core.sampler import ParametrizedQiskitSamplerFactory, SVDQiskitSamplerFactory
from svd.core.task import AdamOptimizationTask
from svd.core.optimizer import AdamOptimizer, UnitLRScheduler
from svd.core.exact_cost import SVDExactCost
from svd.core.encoder import Encoder
from svd.core.circuit import HadamardAndMeausre
from svd.util import pickup
import svd.constant as const
from argparse import ArgumentParser


def do_learn(args, date_index):
    min, filename, data_layer = pickup(date_index, args.prefix)
    data_qubit = const.DATA_QUBITS
    if args.prefix == const.NAIVE_PREFIX:
        data_qubit = const.DATA_QUBITS - 1
    s_factory = ParametrizedQiskitSamplerFactory(data_layer, data_qubit)
    data_sampler = s_factory.load(const.MODEL_PATH + "/" + filename)
    if not args.prefix == const.NAIVE_PREFIX:
        data_sampler.circuit.additional_circuit = HadamardAndMeausre(0)  # do Hadamard transform and measure 0-th qubit
    factory = SVDQiskitSamplerFactory(args.layer, data_sampler.circuit)
    sampler = factory.generate_ten(const.SVD_LOCAL_QUBITS, const.SVD_LOCAL_QUBITS)
    if not args.prefix == const.NAIVE_PREFIX:
        data_sampler.circuit.additional_circuit = HadamardAndMeausre(0)  # do Hadamard transform and measure 0-th qubit
        sampler.post_select = {0: 1}
    optimizer = AdamOptimizer(scheduler=UnitLRScheduler(args.lr), maxiter=args.iter)
    cost = SVDExactCost(const.SVD_LOCAL_QUBITS, const.SVD_LOCAL_QUBITS, Encoder(const.SVD_QUBITS))
    task = AdamOptimizationTask(sampler, cost, optimizer)
    task.optimize()
    factory.save("{}/{}".format(const.SVD_MODEL_PATH, filename), sampler,
                 extra={"cost": cost.value(sampler), const.LAYER_KEY: args.layer})


def learn(args):
    for date_index in range(args.ds, args.de + 1):
        do_learn(args, date_index)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-i", "--iter", help='# of iterations in a trial', type=int, default=500)
    parser.add_argument("-t", "--trial", help='# of trials', type=int, default=1)
    parser.add_argument("-l", "--layer", help='# of layers', type=int, default=8)
    parser.add_argument("-ds", help='start date index', type=int, default=0)
    parser.add_argument("-de", help='end of date index', type=int, default=7)
    parser.add_argument("--prefix", help='prefix of the model and the energy files', default=const.DEFAULT_PREFIX)
    parser.add_argument("-lr", help='learning rate', type=int, default=0.01)
    args = parser.parse_args()
    print(args)
    learn(args)
