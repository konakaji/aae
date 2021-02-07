import sys, warnings

sys.path.append("../")
warnings.filterwarnings('ignore')

from argparse import ArgumentParser
from matplotlib import pyplot
import svd.constant as const


def plot(prefix, label, marker):
    with open("{}/{}.txt".format(const.ENTROPY_PATH, prefix)) as f:
        xs = []
        values = []
        for l in f.readlines():
            x, value = l.rstrip().split("\t")
            xs.append(x)
            values.append(float(value))
    pyplot.plot(xs, values, label=label, marker=marker, markersize=10)


if __name__ == '__main__':
    markers = ["s", "x", "-", "o"]
    label_map = {const.CLASSICAL_PREFIX: "exact", const.NAIVE_PREFIX: "naive",
                 const.DEFAULT_PREFIX: "our algorithm"}
    parser = ArgumentParser()
    parser.add_argument("-ds", help='start date index', type=int, default=0)
    parser.add_argument("-de", help='end of date index', type=int, default=7)
    parser.add_argument("--prefixes", help='list of prefixes of the model and the energy files', nargs='*',
                        default=const.DEFAULT_ENTROPY_PREFIXES)
    args = parser.parse_args()
    pyplot.figure(facecolor="white", edgecolor="black", linewidth=1, figsize=[20, 8])
    pyplot.tick_params(labelsize=16)
    pyplot.title('Transition of the SVD Entropy', fontsize=18)
    pyplot.xlabel("date", fontsize=20)
    pyplot.ylabel("the SVD Entropy", fontsize=20)
    pyplot.ylim([0.2, 1.4])
    pyplot.grid(which='major', color='black', linestyle='-')
    for i, prefix in enumerate(args.prefixes):
        if prefix in label_map:
            label = label_map[prefix]
        else:
            label = prefix
        plot(prefix, label, markers[i % len(markers)])
    pyplot.legend(fontsize=16)
    pyplot.savefig("figure/fig_svd_entropy.eps")
    pyplot.savefig("figure/fig_svd_entropy.png")
