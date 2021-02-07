from svd.finance.context import Context
from svd.finance.entity import StateCoefficient
from svd.core.sampler import ParametrizedQiskitSamplerFactory
from svd.core.util import print_state_tex, num_to_bitarray
from svd.core.encoder import Encoder
from svd.learn_svd import pickup, HadamardAndMeausre
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

if __name__ == '__main__':
    context = Context()
    usecase = context.get_coefficient_usecase()
    for i in range(0, 8):
        coefficient: StateCoefficient = usecase.load(5, i, sub=4)
        min, filename, layer_count = pickup(i, "default")
        s_factory = ParametrizedQiskitSamplerFactory(layer_count, 5)
        data_sampler = s_factory.load("{}/{}".format(const.MODEL_PATH, filename))
        print(filename)
        data_sampler.circuit.additional_circuit = HadamardAndMeausre(0)
        data_sampler.post_select = {0 : 1}
        print(r"{}({})\t{}".format(i, "target", print_state_tex(coefficient.data.flatten(), 4)))
        while True:
            v = data_sampler.get_state_vector()
            correct = is_correct(v, 4, 1, 5)
            if correct:
                vector = post_select(v, 4, 1, 5)
                break
        print(r"{}({})\t{}".format(i, "built", print_state_tex(vector, 4)))