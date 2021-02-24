from itertools import permutations
import pennylane as qml
import numpy as np
import time
import os
from blessed import Terminal


VALIDATE_A_REG = True


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
    def __init__(self, reg_a_size, reg_b_size, ancilla_size, gateSet):
        self.gateSet = gateSet
        self.reg_a_size = reg_a_size
        self.reg_b_size = reg_b_size
        self.ancilla_size = ancilla_size
        self.dev = qml.device(
            "default.qubit", wires=self.reg_a_size + self.reg_b_size + self.ancilla_size)

    def circuit(self, a, b):
        aBasis = i_to_basis(a, pad=self.reg_a_size)
        bBasis = i_to_basis(b, pad=self.reg_a_size)
        zeros = [0] * (self.reg_b_size - self.reg_a_size)
        ancilla = [0] * (self.ancilla_size)
        qml.BasisState(np.array(aBasis + zeros + bBasis + ancilla), wires=range(
            self.reg_a_size + self.reg_b_size + self.ancilla_size))

        for g in self.gateSet:
            if len(g) == 1:
                qml.PauliX(g[0])
            if len(g) == 2:
                qml.CNOT(wires=list(g))
            if len(g) == 3:
                qml.Toffoli(wires=list(g))

        return [qml.expval(qml.PauliZ(i)) for i in range(self.reg_a_size + self.reg_b_size)]

    def draw(self):
        circuit = qml.QNode(self.circuit, self.dev)
        circuit(0, 0)
        return circuit.draw()

    def execute(self, circuit, a, b):
        results = circuit(a, b)
        for i in range(len(results)):
            if results[i] == -1:
                results[i] = 1
            elif results[i] == 1:
                results[i] = 0
            else:
                raise Exception("this shouldn't be possible")

        aOut = basis_to_i((results[0:self.reg_a_size]))
        bOut = basis_to_i(
            (results[self.reg_a_size:self.reg_a_size + self.reg_b_size]))

        return (aOut, bOut)

    def max_score(self):
        return (2**(self.reg_a_size))**2

    def score(self):
        circuit = qml.QNode(self.circuit, self.dev)

        correct = 0
        for a in range((2 ** self.reg_a_size)):
            for b in range((2 ** self.reg_a_size)):
                aOut, bOut = self.execute(circuit, a, b)
                if (a*b) == bOut and (a == aOut or not VALIDATE_A_REG):
                    correct += 1
        return correct

    def results(self):
        circuit = qml.QNode(self.circuit, self.dev)

        results = []
        for a in range((2 ** self.reg_a_size)):
            for b in range((2 ** self.reg_a_size)):
                aOut, bOut = self.execute(circuit, a, b)

                results.append((a, b, aOut, bOut))

        return results


class CircuitGenerator():
    def __init__(self, sizeA, sizeB, ancillaSize):
        self.sizeA = sizeA
        self.sizeB = sizeB
        self.ancillaSize = ancillaSize

        self.generator = self.init_generator()
        self.gate_count = 1

        self.current_perm_size = 0
        self.current_perm_count = 0

    def get_gate_count(self):
        return self.gate_count

    def next(self):
        return next(self.generator)

    def init_generator(self):
        threeWirePerms = list(permutations(
            range(self.sizeA + self.sizeB + self.ancillaSize), 3))

        twoWirePerms = list(permutations(
            range(self.sizeA + self.sizeB + self.ancillaSize), 2))

        oneWirePerms = list(permutations(
            range(self.sizeA + self.sizeB + self.ancillaSize), 1))

        allPerms = oneWirePerms + twoWirePerms + threeWirePerms

        self.gate_count = 1
        while self.gate_count < len(allPerms):
            gateSets = permutations(allPerms, self.gate_count)

            self.current_perm_size = sum(
                [1 for a in permutations(allPerms, self.gate_count)])
            self.current_perm_count = 0

            for gateSet in gateSets:
                self.current_perm_count += 1
                yield gateSet
            self.gate_count += 1


class BruteForcer():
    def __init__(self, N, A):
        self.shots = 0
        self.register_size = N
        self.ancilla_size = A
        self.generator = CircuitGenerator(
            self.register_size, calculate_b_size(
                self.register_size), self.ancilla_size)

        self.bestCircuit = 0
        self.bestCircuitScore = -1

        self.recentCircuit = 0

        self.maxScore = (2**(N))**2

    def isDone(self):
        return self.bestCircuitScore == self.maxScore

    def run(self):
        gateSet = self.generator.next()
        c = Circuit(self.register_size, calculate_b_size(
            self.register_size), self.ancilla_size, gateSet)

        score = c.score()
        self.recentCircuit = c

        # print("---------------")
        # print("Score", score)
        # c.print()
        # print(c.results())

        if score > self.bestCircuitScore:
            # print("New Best", score, self.maxScore)
            self.bestCircuit = c
            self.bestCircuitScore = score
            # print(c.draw())
            # print(c.results())

            if score == self.maxScore:
                print("ALL DONE!")

        self.shots += 1


def calculate_b_size(reg_a_size):
    m = (2**reg_a_size)-1
    return len(i_to_binary(m**2))


class Display():
    def __init__(self, b):
        self.bf = b
        self.start = time.time()
        self.lastDisplay = time.time()
        self.lastShots = 0

        self.term = Terminal()

        self.title_color = self.term.turqoiuse1
        self.label_color = self.term.snow4

        print(self.term.home + self.term.clear)

    # move line, column
    def drawBorder(self, topLeftColumn, topLeftLine, bottomRightColumn, bottomRightLine, title=""):
        print(self.term.move(topLeftLine, topLeftColumn) + "+" +
              "".join(["-"] * (bottomRightColumn-topLeftColumn-1)) + "+")

        if len(title) != 0:
            print(self.term.move(topLeftLine, topLeftColumn+2) +
                  self.term.turquoise1 + " " + title + " " + self.term.normal)

        for y in range(topLeftLine+1, bottomRightLine):
            print(self.term.move(y, topLeftColumn) + "|")
            print(self.term.move(y, bottomRightColumn) + "|")

        print(self.term.move(bottomRightLine, topLeftColumn) + "+" +
              "".join(["-"] * (bottomRightColumn-topLeftColumn-1)) + "+")

    def update(self):

        # print(self.term.home + self.term.clear)
        print(self.term.move(0, 45) + self.term.mediumpurple +
              "mulbrute v0.1" + self.term.normal)

        duration = time.time() - self.start

        po = (2, 2)
        self.drawBorder(po[0], po[1], po[0]+48, po[0] +
                        3, title="process timing")
        print(self.term.move(po[0]+1, po[1]+2) + self.label_color + " run time : "+self.term.normal+"{:.0f} hrs, {:.0f} mins, {:.0f} sec".format(
            duration//3600, duration // 60, duration % 60))
        print(self.term.move(po[0]+2, po[1]+2) + self.label_color + "last best : "+self.term.normal+"{:.0f} hrs, {:.0f} mins, {:.0f} sec".format(
            duration//3600, duration // 60, duration % 60))

        eo = (2, 50)  # line, column
        self.drawBorder(eo[1], eo[0], eo[1] + 50,
                        eo[0] + 5, title="executions")
        # print(self.term.move(eo[0], eo[1]) + "executions")
        print("{}{}    circuits tested :{} {}".format(self.term.move(
            eo[0]+1, eo[1] + 2), self.label_color, self.term.normal, self.bf.shots))
        print("{}{} circuit executions :{} {}".format(self.term.move(
            eo[0]+2, eo[1] + 2), self.label_color, self.term.normal, self.bf.shots * (2**(self.bf.register_size))**2))
        print("{}{}       circuit rate :{} {:.02f} / sec".format(self.term.move(
            eo[0]+3, eo[1] + 2), self.label_color, self.term.normal, (b.shots-self.lastShots) /
            (time.time()-self.lastDisplay)))
        print("{}{}     execution rate :{} {:.02f} / sec".format(self.term.move(
            eo[0]+4, eo[1] + 2), self.label_color, self.term.normal, (b.shots-self.lastShots) * (2**(b.register_size))**2 /
            (time.time()-self.lastDisplay)))

        # print(self.term.move(eo[0]+1, eo[1]+2) + self.label_color +
        #   "    circuits tested :" + self.term.normal, b.shots)
        # print(self.term.move(eo[0]+2, eo[1]+2) + self.label_color +
        #       "circuits executions :" + self.term.normal, b.shots * (2**(b.register_size))**2)
        # print(self.term.move(eo[0]+3, eo[1]+2) + self.label_color + "      circuits rate :" + self.term.normal, (b.shots-self.lastShots) /
        #       (time.time()-self.lastDisplay))
        # print(self.term.move(eo[0]+4, eo[1]+2) + self.label_color + "    executions rate :" + self.term.normal, (b.shots-self.lastShots) * (2**(b.register_size))**2 /
        #       (time.time()-self.lastDisplay))

        pao = (5, 2)
        self.drawBorder(pao[1], pao[0], pao[1] + 48,
                        pao[0] + 5, title="params")
        print("{}{} register a size :{} {}".format(self.term.move(
            pao[0]+1, pao[1] + 2), self.label_color, self.term.normal, self.bf.register_size))
        print("{}{} register b size :{} {}".format(self.term.move(
            pao[0]+2, pao[1] + 2), self.label_color, self.term.normal, calculate_b_size(self.bf.register_size)))
        print("{}{}    ancilla size :{} {}".format(self.term.move(
            pao[0]+3, pao[1] + 2), self.label_color, self.term.normal, self.bf.ancilla_size))
        print("{}{}  validate a out :{} {}".format(self.term.move(
            pao[0]+4, pao[1] + 2), self.label_color, self.term.normal, VALIDATE_A_REG))

        pro = (7, 50)
        self.drawBorder(pro[1], pro[0], pro[1] + 50,
                        pro[0] + 4, title="progress")
        print("{}{}                 gate length :{} {}".format(self.term.move(
            pro[0]+1, pro[1] + 2), self.label_color, self.term.normal, self.bf.generator.get_gate_count()))
        print("{}{}   current permutation count :{} {}".format(self.term.move(
            pro[0]+2, pro[1] + 2), self.label_color, self.term.normal, self.bf.generator.current_perm_size))
        print("{}{} remaining permutation count :{} {}".format(self.term.move(
            pro[0]+3, pro[1] + 2), self.label_color, self.term.normal, self.bf.generator.current_perm_size-self.bf.generator.current_perm_count))

        bo = (12, 2)
        lines = self.bf.bestCircuit.draw().split("\n")

        self.drawBorder(bo[1], bo[0], bo[1] + 98,
                        bo[0] + len(lines), title="best circuit")

        for y in range(len(lines)):
            if lines[y].strip() != "":
                print(self.term.move(bo[0] + y + 1,
                                     bo[1] + 2) + " " + lines[y].strip())

        bro = (bo[0]+1, 40)
        results = b.bestCircuit.results()
        for i in range(len(results)):
            r = results[i]
            line = i // 4
            column = i % 4
            isCorrect = r[0] * r[1] == r[3]
            color = self.term.green
            if not isCorrect:
                color = self.term.red

            out = "{} * {} = {}{}{}".format(r[0],
                                            r[1], color, r[2], self.term.normal)

            print(self.term.move(bro[0] + line, bro[1] + (column * 15)), out)
        print("{}{} score :{} {}".format(self.term.move(
            bro[0]+int(len(results)/4) + 1, bro[1]), self.label_color, self.term.normal, str(b.bestCircuitScore) + " / " + str(b.bestCircuit.max_score())))

        # random ciccuit
        ro = (bo[0] + len(lines) + 1, 2)
        lines = self.bf.recentCircuit.draw().split("\n")

        self.drawBorder(ro[1], ro[0], ro[1] + 98,
                        ro[0] + len(lines), title="recent circuit")

        for y in range(len(lines)):
            if len(lines[y].strip()) != 0:
                print(self.term.move(ro[0] + y + 1,
                                     ro[1] + 2) + " " + lines[y].strip() + "   ")

        rro = (ro[0]+1, 40)
        results = b.recentCircuit.results()
        for i in range(len(results)):
            r = results[i]
            line = i // 4
            column = i % 4
            isCorrect = r[0] * r[1] == r[3]
            color = self.term.green
            if not isCorrect:
                color = self.term.red

            out = "{} * {} = {}{}{}".format(r[0],
                                            r[1], color, r[2], self.term.normal)

            print(self.term.move(rro[0] + line, rro[1] + (column * 15)), out)
        print("{}{} score :{} {}".format(self.term.move(
            rro[0]+int(len(results)/4) + 1, rro[1]), self.label_color, self.term.normal, str(b.recentCircuit.score()) + " / " + str(b.bestCircuit.max_score())))

        self.lastShots = b.shots
        self.lastDisplay = time.time()


if __name__ == "__main__":
    assert i_to_binary(3) == "11"
    assert i_to_binary(3, pad=5) == "00011"

    assert i_to_basis(3) == [1, 1]
    assert basis_to_i([1, 1]) == 3
    assert basis_to_i([1, 0]) == 2
    assert basis_to_i([0]) == 0

    assert calculate_b_size(1) == 1
    assert calculate_b_size(2) == 4

    solutions = SolutionTable(2)
    assert solutions.get(1, 2) == "10"
    assert solutions.get(3, 1, pad=5) == "00011"

    register_size = 1
    ancilla_size = 1

    b = BruteForcer(register_size, ancilla_size)
    d = Display(b)
    while not b.isDone():

        b.run()

        if b.shots % 10 == 1:
            d.update()
    d.update()
    print("All Done")
