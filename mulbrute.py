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
    return int("".join([str(int(c)) for c in b]), 2)


class Circuit():
    def __init__(self, aSize, bSize, gates):
        self.gates = gates
        self.aSize = aSize
        self.bSize = bSize
        self.dev = qml.device(
            "default.qubit", wires=self.aSize + self.bSize)

    def circuit(self, a, b):
        aBasis = i_to_basis(a, pad=self.aSize)
        bBasis = i_to_basis(b, pad=self.aSize)
        zeros = [0] * (self.bSize - self.aSize)
        qml.BasisState(np.array(aBasis + zeros + bBasis), wires=range(
            self.aSize + self.bSize))

        for g in self.gates:
            qml.CNOT(wires=[g[0], g[1]])

        return [qml.expval(qml.PauliZ(i)) for i in range(self.aSize + self.bSize)]

    def print(self):
        circuit = qml.QNode(self.circuit, self.dev)
        circuit(1, 1)
        print(circuit.draw())

    def execute(self, circuit, a, b):
        results = circuit(a, b)
        for i in range(len(results)):
            if results[i] == -1:
                results[i] = 1
            elif results[i] == 1:
                results[i] = 0
            else:
                raise Exception("this shouldn't be possible")

        aOut = basis_to_i((results[0:self.aSize]))
        bOut = basis_to_i((results[self.aSize:]))

        return (aOut, bOut)

    def test(self):
        circuit = qml.QNode(self.circuit, self.dev)

        correct = 0
        for a in range((2 ** self.aSize)):
            for b in range((2 ** self.aSize)):
                aOut, bOut = self.execute(circuit, a, b)
                if (a*b) == bOut and aOut == a:
                    correct += 1
        return correct

    def results(self):
        circuit = qml.QNode(self.circuit, self.dev)

        results = []
        for a in range((2 ** self.aSize)):
            for b in range((2 ** self.aSize)):
                aOut, bOut = self.execute(circuit, a, b)

                results.append((a, b, aOut, bOut))

        return results


class CircuitGenerator():
    def __init__(self, sizeA, sizeB):
        self.sizeA = sizeA
        self.sizeB = sizeB

        self.generator = self.generateCircuits()

    def next(self):
        return next(self.generator)

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


class BruteForcer():
    def __init__(self, N):
        self.shots = 0
        self.N = N
        self.generator = CircuitGenerator(N, N+N)

        self.bestGateSet = 0
        self.bestGateSetScore = 0

        self.maxScore = 2 * 2**N

    def run(self):
        gateSet = self.generator.next()
        c = Circuit(self.N, self.N*2, gateSet)
        score = c.test()

        if score > self.bestGateSetScore:
            print("New Best", score, self.maxScore)
            self.bestGateSet = gateSet
            self.bestGateSetScore = score
            c.print()
            print(c.results())

            if score == self.maxScore:
                print("ALL DONE!")

        self.shots += 1
        if self.shots % 100 == 0:
            print(self.shots)
            c.print()


if __name__ == "__main__":
    assert i_to_binary(3) == "11"
    assert i_to_binary(3, pad=5) == "00011"

    assert i_to_basis(3) == [1, 1]
    print(basis_to_i([1, 1]))
    assert basis_to_i([1, 1]) == 3
    assert basis_to_i([1, 0]) == 2
    assert basis_to_i([0]) == 0

    solutions = SolutionTable(2)
    assert solutions.get(1, 2) == "10"
    assert solutions.get(3, 1, pad=5) == "00011"

    N = 1

    b = BruteForcer(N)
    while True:
        b.run()
