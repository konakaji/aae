import math
from abc import abstractmethod


class Kernel:
    @abstractmethod
    def value(self, x, y):
        return 0


class GaussianKernel(Kernel):
    def __init__(self, sigma):
        self.sigma = sigma

    def value(self, x, y):
        return math.exp(- pow(x - y, 2) / (self.sigma * self.sigma))
