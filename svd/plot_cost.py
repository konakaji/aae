import matplotlib.pyplot as pyplot, os

def plot(filename, key):
    pyplot.clf()
    with open("output/" + filename) as f:
        steps = []
        converted = []
        not_converted = []
        for l in f.readlines():
            if not l.__contains__(key):
                continue
            step, name, value = l.rstrip().split("\t")
            if name.__contains__("(Converted)"):
                steps.append(int(step))
                converted.append(float(value))
            else:
                not_converted.append(float(value))
        pyplot.xlabel("iteration")
        pyplot.ylabel("cost value")
        pyplot.title('Transition of {} Loss'.format(key), fontsize=18)
        pyplot.grid(which='major', color='black', linestyle='-')
        pyplot.plot(steps, converted, label=r"$(A)$")
        pyplot.plot(steps, not_converted, label=r"$(B)$")
        pyplot.legend()
        pyplot.savefig("figure/{}-{}.png".format(key, filename))

if __name__ == '__main__':
    filenames = []
    for filename in os.listdir("output"):
        if not filename.startswith("energy"):
            continue
        filenames.append(filename)
    for filename in filenames:
        plot(filename, "MMD")
        plot(filename, "KL")