import sys, warnings
sys.path.append("../")
warnings.filterwarnings('ignore')

from svd.compute_entropy import do_compute_classical
from svd.finance.context import Context
from svd.finance.entity import StateCoefficient
from svd.core.sampler import ParametrizedQiskitSamplerFactory
from svd.core.util import print_state_tex
from svd.core.encoder import Encoder
from svd.learn_svd import pickup, HadamardAndMeausre
from argparse import ArgumentParser
import svd.constant as const


def post_select(state_vector, i, bit, n_qubit):
    results = []
    encoder = Encoder(n_qubit)
    for num, amplitude in enumerate(state_vector):
        array = encoder.encode(num)
        if array[i] != bit:
            continue
        new_array = []
        for j, a in enumerate(array):
            if j == i:
                continue
            new_array.append(a)
        results.append(amplitude)
    return results


def is_correct(state_vector, i, bit, n_qubit):
    encoder = Encoder(n_qubit)
    for num, amplitude in enumerate(state_vector):
        array = encoder.encode(num)
        if array[i] != bit and amplitude != 0:
            return False
    return True


def do_compare(f, prefix, i, coefficient):
    min, filename, layer_count = pickup(i, prefix)
    print(min, filename)
    f.write("{}({})\t{}\n".format(i, "target", print_state_tex(coefficient.data.flatten(), 4)))
    if prefix == const.NAIVE_PREFIX:
        s_factory = ParametrizedQiskitSamplerFactory(layer_count, const.DATA_QUBITS - 1)
        data_sampler = s_factory.load("{}/{}".format(const.MODEL_PATH, filename))
        vector = data_sampler.get_state_vector()
        f.write("{}({})\t{}\n".format(i, "learned", print_state_tex(vector, 4)))
    else:
        s_factory = ParametrizedQiskitSamplerFactory(layer_count, const.DATA_QUBITS)
        data_sampler = s_factory.load("{}/{}".format(const.MODEL_PATH, filename))
        data_sampler.circuit.additional_circuit = HadamardAndMeausre(0)
        data_sampler.post_select = {0: 1}
        while True:
            v = data_sampler.get_state_vector()
            correct = is_correct(v, 4, 1, const.DATA_QUBITS)
            if correct:
                vector = post_select(v, 4, 1, const.DATA_QUBITS)
                break
        f.write("{}({})\t{}\n".format(i, "learned", print_state_tex(vector, 4)))
    result = []
    r = []
    for v in vector:
        if len(r) % 4 == 0:
            r = []
            result.append(r)
        r.append(v.real)
    print("target", do_compute_classical(coefficient))
    print("learned", do_compute_classical(StateCoefficient(result)))


def compare(args):
    context = Context()
    usecase = context.get_coefficient_usecase()
    with open("{}/{}.txt".format(const.COEFFICIENT_PATH, args.prefix), "w") as f:
        for i in range(args.ds, args.de + 1):
            coefficient: StateCoefficient = usecase.load(5, i, sub=4)
            do_compare(f, args.prefix, i, coefficient)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-ds", help='start date index', type=int, default=0)
    parser.add_argument("-de", help='end of date index', type=int, default=7)
    parser.add_argument("--prefix", help='a prefix of the model and the energy files',
                        default=const.DEFAULT_PREFIX)
    args = parser.parse_args()
    compare(args)
