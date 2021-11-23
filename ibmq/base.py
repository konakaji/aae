import os
from qiskit import IBMQ

TRONTO = "ibmq_toronto"


def find_key():
    dir = os.path.dirname(__file__)
    with open("{}/{}".format(dir, ".ibmq_key")) as f:
        code = f.readline().rstrip()
    return code


def prepare(reservation=False):
    code = find_key()
    IBMQ.save_account(code)
    IBMQ.load_account()
    if reservation:
        p = IBMQ.get_provider(hub='ibm-q-utokyo', group='keio-internal', project='reservations')
    else:
        p = IBMQ.get_provider(hub='ibm-q-utokyo', group='keio-internal', project='keio-students')
    return p


def get_backend(name, reservation=False):
    p = prepare(reservation)
    print(p.backends())
    return p.get_backend(name)


def get_backends(reservation=False):
    p = prepare(reservation)
    return p.backends()


class DeviceFactory:
    def __init__(self, name, reservation):
        self.name = name
        self.reservation = reservation

    def get_backend(self):
        p = prepare(reservation=self.reservation)
        print(p.backends())
        return p.get_backend(name=self.name)
