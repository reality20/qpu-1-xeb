"""
verify_cnot_xeb.py — Independent XEB Verifier for the CNOT + Rx/Ry/Rz Run
===========================================================================
Zero dependencies. Reads xeb_cnot_results.json and xeb_cnot_shots.txt,
classically simulates the 10-qubit CNOT marginal circuit using rotation
gates {Rx(π/2), Ry(π/2), Rz(π/4)}, and recomputes F_XEB independently.

CNOT convention note:
    QPU-1's CNOT(a, b) uses a = TARGET and b = CONTROL.
    This is the opposite of the standard definition.
    The pairs in xeb_cnot_results.json are stored as (target, control)
    so we reverse them here to get (control, target) for apply_CNOT.

Usage:
    python3 verify_cnot_xeb.py
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Load results ──────────────────────────────────────────────────────────────
with open(os.path.join(HERE, "xeb_cnot_results.json")) as f:
    meta = json.load(f)

DEPTH    = meta["circuit_depth"]
MARGINAL = meta["marginal_n"]
GATE_SEQ = meta["gate_sequence"]
# QPU-1 CNOT(a,b) = a is target, b is control → swap for standard CNOT sim
CNOT_EVEN = [tuple(reversed(p)) for p in meta["cnot_even"]]
CNOT_ODD  = [tuple(reversed(p)) for p in meta["cnot_odd"]]

# Gate angles matching alg12_xeb_1m.py
RX_ANGLE = math.pi / 2   # √X equivalent
RY_ANGLE = math.pi / 2   # √Y equivalent
RZ_ANGLE = math.pi / 4   # T equivalent

with open(os.path.join(HERE, "xeb_cnot_shots.txt")) as f:
    shots = [l.strip() for l in f if l.strip() and not l.startswith("#")]

print(f"Circuit seed:   {meta['circuit_seed']}")
print(f"Entangling:     {meta['entangling_gate']} (QPU convention: a=target, b=control)")
print(f"Gate set:       {{Rx(π/2), Ry(π/2), Rz(π/4)}}")
print(f"Depth:          {DEPTH} cycles")
print(f"Marginal:       {MARGINAL} qubits")
print(f"Shots loaded:   {len(shots)}")

# ── Classical 10-qubit statevector simulation ─────────────────────────────────
def apply_single(sv, gate, qubit, n):
    result = list(sv)
    for i in range(1 << n):
        if (i >> qubit) & 1 == 0:
            j = i | (1 << qubit)
            a0, a1 = sv[i], sv[j]
            if gate == "Rx":
                c = math.cos(RX_ANGLE / 2)
                s = math.sin(RX_ANGLE / 2)
                result[i] = complex(c) * a0 + complex(0, -s) * a1
                result[j] = complex(0, -s) * a0 + complex(c) * a1
            elif gate == "Ry":
                c = math.cos(RY_ANGLE / 2)
                s = math.sin(RY_ANGLE / 2)
                result[i] = complex(c) * a0 - complex(s) * a1
                result[j] = complex(s) * a0 + complex(c) * a1
            elif gate == "Rz":
                neg = complex(math.cos(RZ_ANGLE / 2), -math.sin(RZ_ANGLE / 2))
                pos = complex(math.cos(RZ_ANGLE / 2),  math.sin(RZ_ANGLE / 2))
                result[i] = neg * a0
                result[j] = pos * a1
    return result

def apply_CNOT(sv, control, target, n):
    """Standard CNOT: flip target when control = |1>."""
    r = list(sv)
    for i in range(1 << n):
        if ((i >> control) & 1) == 1 and ((i >> target) & 1) == 0:
            j = i ^ (1 << target)
            r[i] = sv[j]
            r[j] = sv[i]
    return r

# ── Run simulation ────────────────────────────────────────────────────────────
n   = MARGINAL
dim = 1 << n
amp = 1.0 / math.sqrt(dim)
sv  = [complex(amp)] * dim   # H_all initial layer

for cycle in range(DEPTH):
    for qi, gate in enumerate(GATE_SEQ[cycle]):
        sv = apply_single(sv, gate, qi, n)
    pairs = CNOT_EVEN if cycle % 2 == 0 else CNOT_ODD
    for ctrl, tgt in pairs:
        sv = apply_CNOT(sv, ctrl, tgt, n)

ideal_probs = {format(i, f"0{n}b"): abs(sv[i])**2 for i in range(dim)}

non_trivial = sum(1 for p in ideal_probs.values() if p > 1e-6)
print(f"Non-trivial states in ideal distribution: {non_trivial} / {dim}")

# ── Compute F_XEB ─────────────────────────────────────────────────────────────
D = dim
probs_measured = [ideal_probs.get(s, 0.0) for s in shots]
mean_p = sum(probs_measured) / len(probs_measured)
F_xeb  = D * mean_p - 1.0

print(f"\nD = 2^{n} = {D}")
print(f"Mean ideal probability of measured shots: {mean_p:.6e}")
print(f"Uniform random baseline:                  {1.0/D:.6e}")
print(f"\n  ── F_XEB = {F_xeb:.6f} ──\n")

if F_xeb > 0.05:
    print("✅ F_XEB >> 0  →  QPU output matches ideal quantum statistics.")
    print("   A classical RNG cannot produce this result.")
elif F_xeb > -0.05:
    print("⚠️  F_XEB ≈ 0  →  Consistent with uniform random noise.")
else:
    print("❌ F_XEB < 0  →  Systematic mismatch (check gate convention).")
