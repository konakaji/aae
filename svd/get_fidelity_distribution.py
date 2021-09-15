from svd.extention.data_learning import DataLearning
from svd.finance.context import Context
from svd import constant as const
import numpy as np
import os

if __name__ == '__main__':
    context = Context()
    usecase = context.get_coefficient_usecase()
    with open('output/fidelity.txt', 'w') as w:
        for i in range(0, 8):
            coefficient = usecase.load(const.TIME_SPAN, i, sub=const.STOCK_COUNT)
            dl = DataLearning(5, 8)
            fidelities = []
            others = []
            for filename in os.listdir('output/data_model'):
                if filename.startswith('eight-{}'.format(i)):
                    with open('output/energy/{}'.format(filename)) as f:
                        lines = f.readlines()
                        energy1 = float(lines[len(lines) - 2].split('\t')[2])
                        energy2 = float(lines[len(lines) - 1].split('\t')[2])
                    dl.load(filename)
                    fidelity = abs(np.array(dl.get_state_vector()).dot(coefficient.to_state()).real)
                    if energy1 < 0.01 and energy2 < 0.01:
                        fidelities.append(fidelity)
                    else:
                        others.append(fidelity)
            w.write('{}\n'.format(','.join([str(v) for v in
                                            [len(fidelities), '{:.3f}'.format(np.min(fidelities)), '{:.3f}'.format(np.mean(fidelities)),
                                             '{:.3f}'.format(np.max(fidelities)), len(others),
                                             '{:.3f}'.format(np.mean(others)),
                                             '{:.3f}'.format(np.max(others))]])))
