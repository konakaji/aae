import os, numpy

if __name__ == '__main__':
    for i in range(0, 8):
        costs = []
        for filename in os.listdir('output/energy'):
            if filename.startswith('eight-{}'.format(i)):
                with open('output/energy/{}'.format(filename)) as f:
                    lines = f.readlines()
                    cost = (float(lines[len(lines) - 2].split('\t')[2]) + float(
                        lines[len(lines) - 1].split('\t')[2])) / 2
                    costs.append(cost)
        print(numpy.mean(costs), numpy.std(costs), numpy.min(costs))
