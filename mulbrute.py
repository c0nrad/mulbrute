from itertools import permutations
import pennylane as qml
import numpy as np
import time
import os


class SolutionTable():
    def __init__(self, size):
        self.size = 2

    def get(self, a, b, pad=0):
        if len(i_to_binary(a)) > self.size:
            raise Exception("invalid register size", a, self.size)

        if len(i_to_binary(b)) > self.size:
            raise Exception("invalid register size", b, self.size)

        return i_to_binary(a * b, pad=pad)


def i_to_binary(a, pad=0):
    out = "{0:b}".format(a)
    return out.zfill(pad)


def i_to_basis(a, pad=0):
    return [int(c) for c in i_to_binary(a, pad)]


def basis_to_i(b):
    out = 0
    for i in range(len(b)):
        if b[i]:
            out += i**2
    return out


class Circuit():

    def __init__(self, aSize, bSize, gates):
        self.gates = gates
        self.aSize = aSize
        self.bSize = bSize

    def test(self):
        dev = qml.device(
            "default.qubit", wires=self.aSize + self.bSize)

        @qml.qnode(dev)
        def circuit():
            aBasis = i_to_basis(a, pad=self.aSize)
            bBasis = i_to_basis(b, pad=self.aSize)
            zeros = np.zeros(self.bSize - self.aSize)
            print(aBasis, zeros)
            qml.BasisState(np.concatenate((np.array(aBasis + bBasis), zeros)), wires=range(
                self.aSize + self.bSize))

            for g in self.gates:
                qml.CNOT(wires=[g[0], g[1]])

            # return qml.expval(qml.PauliZ(0))
            return [qml.expval(qml.PauliZ(i)) for i in range(self.aSize + self.bSize)]

        solutions = SolutionTable(self.aSize)
        allCorrect = True
        for a in range((self.aSize ** 2) - 1):
            for b in range((self.aSize**2) - 1):  # use aSize again

                print("Testing", a, "*", b)

                results = circuit()
                for i in range(len(results)):
                    if results[i] == -1:
                        results[i] = 1
                    elif results[i] == 1:
                        results[i] = 0
                    else:
                        raise Exception("this shouldn't be possible")

                print(results)
                if a == 0 and b == 0:
                    print(circuit.draw())

                aOut = basis_to_i(results[0:self.aSize])
                bOut = basis_to_i(results[self.aSize:])

                if (a*b) == bOut and a = aOut:
                    print("NICE")
                else:
                    allCorrect = False
                    print("Not a valid circuit")
                    return
        print("Holy crap!")
        os.exit(1)


class BruteForcer():
    def __init__(self, sizeA, sizeB):
        self.sizeA = sizeA
        self.sizeB = sizeB

    def generateCircuits(self):
        twoWirePerms = list(permutations(range(self.sizeA + self.sizeB), 2))

        gateCount = 1
        while gateCount < len(twoWirePerms):
            gateSets = permutations(twoWirePerms, gateCount)

            for gateSet in gateSets:
                yield gateSet
            gateCount += 1

    def checkCircuit(self):
        return


if __name__ == "__main__":
    assert i_to_binary(3) == "11"
    assert i_to_binary(3, pad=5) == "00011"

    assert i_to_basis(3) == [1, 1]

    solutions = SolutionTable(2)
    assert solutions.get(1, 2) == "10"
    assert solutions.get(3, 1, pad=5) == "00011"

    b = BruteForcer(2, 4)

    for gateSet in b.generateCircuits():
        print(gateSet)
        c = Circuit(2, 4, gateSet)
        c.test()
