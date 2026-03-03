"""
otoc_echo_qpu.py — QPU-1 OTOC Echo Script (Qreg code only)
===========================================================
This is the actual Qreg code submitted to QPU-1 for the
Quantum Echo / OTOC experiment.

NOTE: H·H = X on QPU-1 (not I). The echo check must look
for all-ones after final H_all, not all-zeros.

Protocol per shot:
  1. reset_all → |0...0⟩
  2. H_all → superposition
  3. Forward U: L cycles of {Rx/Ry/Rz on marginal} + CZ tiles
  4. X on butterfly qubit (skip for baseline)
  5. Backward U†: reverse cycles, CZ then inverse rotations
  6. H_all → on QPU-1 this produces all-ones if U†·U = I
  7. Measure → echo = 1 if marginal is all-ones
"""

import time, math

N_QUBITS       = 1_000_000
MARGINAL_N     = 10
MARGINAL_START = 0
N_SHOTS        = 100
DEPTH          = 8
PERTURB_QUBIT  = -1   # -1 = no perturbation (baseline), 0..9 = butterfly qubit

# Gate angles
RX_ANGLE =  1.5707963267948966   #  π/2
RY_ANGLE =  1.5707963267948966   #  π/2
RZ_ANGLE =  0.7853981633974483   #  π/4

# Gate schedule (seeded for reproducibility)
import random
rng = random.Random(20260303)
GATE_SET = ["Rx", "Ry", "Rz"]
gate_seq = [[rng.choice(GATE_SET) for _ in range(MARGINAL_N)] for _ in range(DEPTH)]

# CZ tile patterns (offset to MARGINAL_START)
s = MARGINAL_START
cz_even = [(s+0,s+1),(s+2,s+3),(s+4,s+5),(s+6,s+7),(s+8,s+9)]
cz_odd  = [(s+0,s+5),(s+1,s+6),(s+2,s+7),(s+3,s+8),(s+4,s+9)]

def apply_fwd(q, qubit, gate):
    if gate == "Rx": q.Rx(qubit, RX_ANGLE)
    elif gate == "Ry": q.Ry(qubit, RY_ANGLE)
    elif gate == "Rz": q.Rz(qubit, RZ_ANGLE)

def apply_inv(q, qubit, gate):
    if gate == "Rx": q.Rx(qubit, -RX_ANGLE)
    elif gate == "Ry": q.Ry(qubit, -RY_ANGLE)
    elif gate == "Rz": q.Rz(qubit, -RZ_ANGLE)

q = Qreg(N_QUBITS)
start = time.time()

for shot in range(N_SHOTS):
    q.reset_all()
    q.H_all()

    # Forward U
    for cy in range(DEPTH):
        for i in range(MARGINAL_N):
            apply_fwd(q, MARGINAL_START + i, gate_seq[cy][i])
        for a, b in (cz_even if cy % 2 == 0 else cz_odd):
            q.CZ(a, b)

    # Perturbation
    if PERTURB_QUBIT >= 0:
        q.X(PERTURB_QUBIT)

    # Backward U†: reversed cycles, CZ first then inverse 1Q gates
    for cy in range(DEPTH - 1, -1, -1):
        for a, b in (cz_even if cy % 2 == 0 else cz_odd):
            q.CZ(a, b)
        for i in range(MARGINAL_N):
            apply_inv(q, MARGINAL_START + i, gate_seq[cy][i])

    # Final H_all (on QPU-1: H·H = X, so echo = all-ones if U†U = I)
    q.H_all()

    bits = q.measure()
    marginal = bits[MARGINAL_START:MARGINAL_START + MARGINAL_N]
    # Check for all-ONES (because H·H = X on QPU-1)
    echo = 1 if all(int(b) == 1 for b in marginal) else 0
    print("ECHO:" + str(echo) + " BITS:" + "".join(str(int(b)) for b in marginal))

elapsed = time.time() - start
print("ELAPSED:" + str(elapsed))
print("DONE")
