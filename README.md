# Determining Efficient Multiplication Circuits via Brute Force

A project for the XanaduAI QHack2021 hackathon. [Submission](https://github.com/XanaduAI/QHack/issues/11)

## Overview

This program brute forces through a large combination of quantum circuits in order to find an efficient multiplication circuit for arbitrary qubit register size.

## Background

It's hard to do multiplication with Quantum Circuits. Current multiplication circuits require a large number of ancilla qubits which we don't have.

The goal of this project is to see if we can make the circuit for "A=A\*B" smaller.

We'll do this by brute forcing over every possible circuit using only PauliX, CNOT, and Toffoli gates, starting from the simplest circuits and getting incrementally harder.

Under the hood it uses python's itertools.permutations library to generate circuits and then pennylane's quantum simulator to test the circuits.

The terminal user interface was written in [blessed](https://blessed.readthedocs.io/en/latest/index.html) and inspired heavily by [afl](https://lcamtuf.coredump.cx/afl/).

## Demo

![demo](/mulbrute_1bit.gif)

### Results

#### 1 bit multiply

So far it's been able to determine two circuits for 1 bit multiplication!

If we allow the first register to be clobbered:

![1_clobber](/1_clobber.png)

If we don't want the first register to be clobbered:

![1_noclobber](1_noclobber.png)

#### 2 bit multiply

Haven't determined this circuit yet.

Progress:
![2_attempt](2_attempt.png)

# Method

Brute force. Basically the algorithm tries every possible combination of PauliX/CNOT/Toffoli gates and checks to see if the results are correct.

For example this gate was randomly created. A = [0,1], B=[2,3,4,5]

```
 0: ──╭|0.0⟩──╭C──────╭C──╭X──┤ ⟨Z⟩
 1: ──├|0.0⟩──│───╭X──│───│───┤ ⟨Z⟩
 2: ──├|0.0⟩──│───│───│───│───┤ ⟨Z⟩
 3: ──├|0.0⟩──╰X──╰C──│───│───┤ ⟨Z⟩
 4: ──├|0.0⟩──────────│───╰C──┤ ⟨Z⟩
 5: ──╰|0.0⟩──────────╰X──────┤ ⟨Z⟩
```

Then I measure a couple of times to see if corresponds to the multiplication table. So I plug in A=01, and B = 10, and then check after the circuit executes if B = 0010.

It uses pennylanes default qubit simulator to check the circuits.

## Pennylane circuit

```python
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
```

# Running

```
pip3 install blessed pennylane
make run
```
