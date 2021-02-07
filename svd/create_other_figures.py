from svd.learn_svd import pickup
from svd.finance.context import Context
from svd.core.sampler import ParametrizedQiskitSamplerFactory, SVDQiskitSamplerFactory
from svd.core.util import ImageGenrator
from svd.core.circuit import AllHadamardCircuit
import qiskit


class HadamardAndMeausre(qiskit.QuantumCircuit):
    def __init__(self, target):
        self.target = target

    def merge(self, circuit: qiskit.QuantumCircuit, q_register: qiskit.QuantumRegister):
        circuit.h(self.target)
        circuit.measure([self.target], [self.target])
        circuit.barrier()
        return circuit, q_register


def plot(start, hadamard):
    context = Context()
    usecase = context.get_coefficient_usecase()
    coefficient = usecase.load(5, start, sub=4)
    probability = coefficient.to_probability()
    model = pickup(start, "5")[1]
    data_factory = ParametrizedQiskitSamplerFactory(6, 5)
    data_sampler = data_factory.load("output/" + model)
    if hadamard:
        data_sampler.circuit.additional_circuit = AllHadamardCircuit(5)
        probability = coefficient.to_hadamard_probability()
        start = start * 100
    generator = ImageGenrator("./quality", probability)
    titles = find_titles(hadamard)
    generator.probability_title = titles[0]
    generator.state_title = titles[1]
    generator.plt_option_func = plot_option_func
    generator.generate(start, data_sampler)


def plot_mmd(start):
    model = pickup(start, "5")[1]
    import matplotlib.pyplot as p
    p.clf()
    with open("output/{}".format(model.replace("model", "energy"))) as f:
        lines = f.readlines()
        mmds = []
        converted_mmds = []
        total_mmds = []
        xs = []
        for line in lines:
            step, name, value = line.split("\t")
            if name == "MMDCost(Converted)":
                mmds.append(float(value))
            elif name == "MMDCost(Non-Converted)":
                converted_mmds.append(float(value))
            if len(mmds) == 201:
                break
        for i, mmd in enumerate(mmds):
            xs.append(i)
            total_mmds.append((mmd + converted_mmds[i]) / 2)
        p.plot(xs, mmds,
               label=r"$\mathcal{L}_{MMD}\left(\tilde{\psi}_k^2,|\langle k|U(\theta)|0\rangle^{\otimes 5}|^2\right)$")
        p.plot(xs, converted_mmds, label=r"$\mathcal{L}_{MMD}\left(\left(\sum_{\ell=0}^{31}"
                                         r"\tilde{\psi}_{\ell}\langle \ell|H^{\otimes 5}|k\rangle\right)^2,"
                                         r"|\langle k|H^{\otimes 5}U(\theta)|0\rangle^{\otimes 5}|^2\right)$")
        p.plot(xs, total_mmds, label=r"$\mathcal{L}$")
        p.tick_params(labelsize=12)
        p.xlabel("iteration", fontsize=12)
        p.ylabel("the value", fontsize=12)
        p.grid(which='major', color='black', linestyle='-')
        p.legend(fontsize=12)
        p.savefig("quality/cost_{}.png".format(start))


def find_titles(hadamard):
    if hadamard:
        return [r"$\left(\sum_{\ell=0}^{31}\tilde{\psi}_{\ell}\langle \ell|H^{\otimes 5}|k\rangle\right)^2$",
                r"$|\langle k|H^{\otimes 5}U(\theta)|0\rangle^{\otimes 5}|^2$"]
    else:
        return [r"$\tilde{\psi}_k^2$", r"$|\langle k|U(\theta)|0\rangle^{\otimes 5}|^2$"]


def plot_option_func(plt):
    plt.tick_params(labelsize=12)
    plt.xlabel("k", fontsize=12)
    plt.ylabel("the value", fontsize=12)
    plt.grid(which='major', color='black', linestyle='-')


def plot_data_circuit():
    model = pickup(99, "5")[1]
    data_factory = ParametrizedQiskitSamplerFactory(6, 5)
    data_sampler = data_factory.load("output/" + model)
    data_sampler.circuit.draw_mode = True
    style = {'gatefacecolor': 'lightgreen', 'latexdrawerstyle': True}
    data_sampler.circuit.to_qiskit().draw("mpl", style=style, plot_barriers=False)
    import matplotlib.pyplot as p
    p.savefig("./quality/fig_data_circuit.png")
    p.savefig("./quality/fig_data_circuit.eps")


def plot_svd_circuit():
    model = pickup(99, "5")[1]
    data_factory = ParametrizedQiskitSamplerFactory(6, 5)
    data_sampler = data_factory.load("output/" + model)
    data_circuit = data_sampler.circuit
    data_circuit.draw_mode = True
    filename = "5composite-" + model + ".txt"
    data_circuit.additional_circuit = HadamardAndMeausre(0)
    c_factory = SVDQiskitSamplerFactory(8, data_circuit)
    sampler = c_factory.load("output/" + filename)
    style = {'gatefacecolor': 'lightgreen', 'latexdrawerstyle': True}
    sampler.circuit.draw_mode = True
    sampler.circuit.parameter_name = "\\xi"
    sampler.circuit.another_parameter_name = "\\xi^{\prime}"
    sampler.draw("mpl", style=style)
    import matplotlib.pyplot as p
    p.savefig("./quality/fig_svd_circuit.png")
    p.savefig("./quality/fig_svd_circuit.eps")


if __name__ == '__main__':
    for start in range(99, 107):
        for hadamard in [False, True]:
            plot(start, hadamard)
        plot_mmd(start)
    plot_data_circuit()
    plot_svd_circuit()
