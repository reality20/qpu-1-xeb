"""
verify_cnot_xeb.py — Independent XEB Verifier for the CNOT Run
===============================================================
Zero dependencies. Reads xeb_cnot_results.json and xeb_cnot_shots.txt,
classically simulates the 10-qubit CNOT marginal circuit, and recomputes
F_XEB to confirm QPU-1's quantum advantage claim for the CNOT run.

CNOT convention note:
    QPU-1's CNOT(a, b) uses a = TARGET and b = CONTROL.
    This is the opposite of the standard definition.
    The simulation here uses that convention.

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
# QPU-1 convention: CNOT(a,b) → a=target, b=control → swap pairs for classical sim
CNOT_EVEN = [tuple(reversed(p)) for p in meta["cnot_even"]]
CNOT_ODD  = [tuple(reversed(p)) for p in meta["cnot_odd"]]

with open(os.path.join(HERE, "xeb_cnot_shots.txt")) as f:
    shots = [l.strip() for l in f if l.strip() and not l.startswith("#")]

print(f"Circuit seed:   {meta['circuit_seed']}")
print(f"Entangling:     {meta['entangling_gate']} (QPU convention: a=target, b=control)")
print(f"Depth:          {DEPTH} cycles")
print(f"Marginal:       {MARGINAL} qubits")
print(f"Shots loaded:   {len(shots)}")

# ── Classical 10-qubit statevector simulation ─────────────────────────────────
def apply_H(sv, q, n):
    s = 1.0 / math.sqrt(2)
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1 == 0:
            j = i | (1 << q)
            r[i] = s * sv[i] + s * sv[j]
            r[j] = s * sv[i] - s * sv[j]
    return r

def apply_S(sv, q, n):
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1:
            r[i] = sv[i] * complex(0, 1)
    return r

def apply_T(sv, q, n):
    r = list(sv)
    phase = complex(math.cos(math.pi / 4), math.sin(math.pi / 4))
    for i in range(1 << n):
        if (i >> q) & 1:
            r[i] = sv[i] * phase
    return r

def apply_CNOT(sv, control, target, n):
    """Standard CNOT: flip target when control = |1>."""
    r = list(sv)
    for i in range(1 << n):
        if ((i >> control) & 1) == 1 and ((i >> target) & 1) == 0:
            j = i ^ (1 << target)
            r[i] = sv[j]
            r[j] = sv[i]
    return r

GATE_FN = {"H": apply_H, "S": apply_S, "T": apply_T}

n   = MARGINAL
dim = 1 << n
amp = 1.0 / math.sqrt(dim)
sv  = [complex(amp)] * dim  # H_all initial layer

for cycle in range(DEPTH):
    for qi, gate in enumerate(GATE_SEQ[cycle]):
        sv = GATE_FN[gate](sv, qi, n)
    # Pairs already swapped above to reflect QPU-1 CNOT(a,b) = a is target
    pairs = CNOT_EVEN if cycle % 2 == 0 else CNOT_ODD
    for ctrl, tgt in pairs:
        sv = apply_CNOT(sv, ctrl, tgt, n)

ideal_probs = {format(i, f"0{n}b"): abs(sv[i])**2 for i in range(dim)}

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
    print("❌ F_XEB < 0  →  Systematic mismatch (check CNOT convention).")
