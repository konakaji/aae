import os, svd.constant as const

if __name__ == '__main__':
    s = set()
    for l in os.listdir(const.ENERGY_PATH):
        s.add(l)
    results = []
    for l in os.listdir(const.MODEL_PATH):
        if l not in s:
            results.append(l)
    results.sort()
    for r in results:
        print(const.MODEL_PATH + "/" + r)
        os.remove(const.MODEL_PATH + "/" + r)