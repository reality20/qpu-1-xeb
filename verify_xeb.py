"""
verify_xeb.py — Independent XEB Fidelity Verifier
===================================================
Zero dependencies. Reads xeb_results.json and xeb_shots.txt,
classically simulates the 10-qubit marginal circuit, and
recomputes F_XEB to confirm QPU-1's quantum advantage claim.

Usage:
    python3 verify_xeb.py
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ── Load results ──────────────────────────────────────────────────────────────
with open(os.path.join(HERE, "xeb_results.json")) as f:
    meta = json.load(f)

SEED      = meta["circuit_seed"]
DEPTH     = meta["circuit_depth"]
MARGINAL  = meta["marginal_n"]
GATE_SEQ  = meta["gate_sequence"]   # list[list[str]]
CZ_EVEN   = [tuple(p) for p in meta["cz_even"]]
CZ_ODD    = [tuple(p) for p in meta["cz_odd"]]

with open(os.path.join(HERE, "xeb_shots.txt")) as f:
    shots = [l.strip() for l in f if l.strip() and not l.startswith("#")]

print(f"Circuit seed:   {SEED}")
print(f"Depth:          {DEPTH} cycles")
print(f"Marginal qubits:{MARGINAL}")
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
    ang = math.pi / 4
    phase = complex(math.cos(ang), math.sin(ang))
    for i in range(1 << n):
        if (i >> q) & 1:
            r[i] = sv[i] * phase
    return r

def apply_CZ(sv, q0, q1, n):
    r = list(sv)
    for i in range(1 << n):
        if ((i >> q0) & 1) and ((i >> q1) & 1):
            r[i] = -r[i]
    return r

GATE_FN = {"H": apply_H, "S": apply_S, "T": apply_T}

n = MARGINAL
dim = 1 << n
amp = 1.0 / math.sqrt(dim)
sv = [complex(amp)] * dim   # H_all initial layer

for cycle in range(DEPTH):
    for qi, gate in enumerate(GATE_SEQ[cycle]):
        sv = GATE_FN[gate](sv, qi, n)
    pairs = CZ_EVEN if cycle % 2 == 0 else CZ_ODD
    for q0, q1 in pairs:
        sv = apply_CZ(sv, q0, q1, n)

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
    print("❌ F_XEB < 0  →  Systematic error in circuit execution.")
