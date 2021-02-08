import sys, warnings

sys.path.append("../")
warnings.filterwarnings('ignore')

from argparse import ArgumentParser
import numpy as np
import math
from svd.core.sampler import SVDQiskitSamplerFactory, ParametrizedQiskitSamplerFactory
from svd.core.encoder import Encoder
from svd.core.circuit import HadamardAndMeausre
from svd.finance.context import Context
from svd.util import pickup, date_format
import svd.constant as const


def do_compute_classical(coefficient):
    result = np.diag(np.zeros(4, dtype=np.complex))
    for i in range(len(coefficient.data)):
        for j in range(len(coefficient.data)):
            for t, c in enumerate(coefficient.data[i]):
                result[i][j] = result[i][j] + c * coefficient.data[j][t]
    r = 0
    for v in np.linalg.eigvalsh(result):
        if v < 0:
            continue
        r = r - v * math.log(v)
    return r


def build_date_map():
    date_map = {}
    with open(const.DATE_PATH) as f:
        for l in f.readlines():
            id, date = l.rstrip().split("\t")
            date_map[int(id)] = date
    return date_map


def compute_classical(index):
    c = Context()
    usecase = c.get_coefficient_usecase()
    coefficient = usecase.load(5, index, sub=4)
    return do_compute_classical(coefficient)


def compute_quantum(index, prefix):
    min_energy, filename, layer_count = pickup(index, prefix)
    data_factory = ParametrizedQiskitSamplerFactory(layer_count, const.DATA_QUBITS)
    data_sampler = data_factory.load("{}/{}".format(const.MODEL_PATH, filename))
    data_circuit = data_sampler.circuit
    if not prefix == const.NAIVE_PREFIX:
        data_circuit.additional_circuit = HadamardAndMeausre(0)
    c_factory = SVDQiskitSamplerFactory(8, data_circuit)
    print(index, filename)
    sampler = c_factory.load("{}/{}".format(const.SVD_MODEL_PATH, filename))
    if not prefix == const.NAIVE_PREFIX:
        sampler.post_select = {0: 1}
    result = 0
    encoder = Encoder(const.SVD_QUBITS)
    for i, p in enumerate(sampler.exact_probabilities()):
        bit_array = encoder.encode(i)
        if bit_array[0] == bit_array[2] and bit_array[1] == bit_array[3]:
            result = result - p * math.log(p)
    return result


def compute(args):
    dates = []
    date_map = build_date_map()
    for i in range(args.ds, args.de + 1):
        dates.append(date_format(date_map[i + 4]))
    for prefix in args.prefixes:
        classical = (prefix == const.CLASSICAL_PREFIX)
        with open("{}/{}.txt".format(const.ENTROPY_PATH, prefix), "w") as f:
            for i in range(args.ds, args.de + 1):
                if classical:
                    f.write("{}\t{}\n".format(dates[i], compute_classical(i)))
                else:
                    f.write("{}\t{}\n".format(dates[i], compute_quantum(i, prefix)))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-ds", help='start date index', type=int, default=0)
    parser.add_argument("-de", help='end of date index', type=int, default=7)
    parser.add_argument("--prefixes", help='list of prefixes of the model and the energy files', nargs='*',
                        default=const.DEFAULT_ENTROPY_PREFIXES)
    args = parser.parse_args()
    compute(args)
