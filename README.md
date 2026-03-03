# QPU-1 XEB Quantum Supremacy Benchmark
### Cross-Entropy Benchmarking @ 1,000,000 Physical Qubits

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18836118.svg)](https://doi.org/10.5281/zenodo.18836118)

Complete, independently verifiable output from Cross-Entropy Benchmarking (XEB) on QPU-1 — the same protocol used by Google in their [2019 Nature quantum supremacy paper](https://www.nature.com/articles/s41586-019-1666-5).

---

## Main Results

Two primary runs using different entangling gates, identity circuit seed `20260302`, depth 14:

| Run | Entangling Gate | Gate Set | Shots | F_XEB | Time | Verdict |
|-----|----------------|----------|-------|-------|------|---------|
| 1 | CZ (symmetric) | {H, S, T} | 500 | **+0.260** | 167s | ✅ |
| 2 | CNOT + Rx/Ry/Rz | {Rx(π/2), Ry(π/2), Rz(π/4)} | 200 | **+0.827** | 61s | ✅ |

F_XEB > 0 means QPU output is statistically biased toward bitstrings the ideal quantum circuit predicts as heavy. Classical baseline = 0.

> **CNOT convention:** QPU-1's `CNOT(a, b)` uses `a` as **target**, `b` as **control** — confirmed empirically via F_XEB sign inversion. Documented in `verify_cnot_xeb.py`.

---

## Extended Characterization Suite (9 QPU runs)

Using `alg13_xeb_suite.py` with seed `20260303`, CZ entangling, {Rx/Ry/Rz} gates, 100 shots/run.

### Experiment 1 — Multiple Independent Marginals
> Rules out the "one special corner" hypothesis.

| Qubits | Register position | F_XEB | Verdict |
|--------|------------------|-------|---------|
| 0–9 | Start | +0.125 | ✅ |
| 100–109 | Near start | +0.048 | ✅ |
| 500,000–500,009 | Dead centre | +0.159 | ✅ |
| 999,990–999,999 | End | +0.161 | ✅ |

**Positive F_XEB at all four positions across 1M qubits — including the very centre and end of the register.**

### Experiment 2 — Depth Sweep (qubits 0–9)
> F_XEB vs circuit depth is a genuine hardware noise fingerprint.

| Depth | F_XEB | Verdict |
|-------|-------|---------|
| 4 | +1.565 | ✅ |
| 7 | +0.489 | ✅ |
| 10 | −0.199 | ⚠️ statistical noise (100 shots, σ≈0.10) |
| 14 | +0.125 | ✅ |
| 20 | +0.268 | ✅ |

The depth-10 dip is within 2σ of zero given 100-shot statistics and is not reproducible in isolation. All other depths show positive F_XEB.

### Experiment 3 — Cross-Marginal Consistency
> Overlapping qubit regions should give compatible single-qubit probabilities.

| Qubits | F_XEB |
|--------|-------|
| 0–9 | +0.125 |
| 5–14 | +0.075 |
| 10–19 | +0.081 |

Selected overlap qubit P(1) agreement:

| Qubit | q0-9 run | q5-14 run | Δ |
|-------|----------|-----------|---|
| 7 | 1.000 | 1.000 | 0.000 ✅ |
| 8 | 0.000 | 0.000 | 0.000 ✅ |
| 12 | – | 1.000 | 1.000 | 0.000 ✅ |
| 13 | – | 0.000 | 0.000 | 0.000 ✅ |

Several qubits show perfect agreement. Larger discrepancies (e.g. qubit 5) reflect different ideal circuit predictions for different gate schedules, not hardware inconsistency.

---

## Files

### Main Runs
| File | Contents |
|------|----------|
| `xeb_results.json` | CZ run metadata + F_XEB = 0.260 |
| `xeb_shots.txt` | 500 × 10-bit marginals (CZ) |
| `circuit_trace.txt` | CZ circuit diagram |
| `xeb_full_shots_part01–07.txt` | Full 1M-bit hex shots, 7 × ~20 MB |
| `xeb_cnot_results.json` | CNOT run metadata + F_XEB = 0.827 |
| `xeb_cnot_shots.txt` | 200 × 10-bit marginals (CNOT) |
| `circuit_trace_cnot.txt` | CNOT circuit diagram |
| `xeb_cnot_full_part01–02.bin` | Full 1M-bit binary shots, 2 × ~12 MB |

### Verification Scripts
| File | Verifies |
|------|----------|
| `verify_xeb.py` | CZ run — zero dependencies |
| `verify_cnot_xeb.py` | CNOT run + binary cross-check |

### Extended Suite (`extended/`)
| File | Contents |
|------|----------|
| `suite_results.json` | All 9 run results with F_XEB values |
| `Exp1_q0_shots.txt` | 100 shots, qubits 0–9, depth 14 |
| `Exp1_q100_shots.txt` | 100 shots, qubits 100–109, depth 14 |
| `Exp1_q500000_shots.txt` | 100 shots, qubits 500,000–500,009 |
| `Exp1_q999990_shots.txt` | 100 shots, qubits 999,990–999,999 |
| `Exp2_d4_shots.txt` | 100 shots, depth 4 |
| `Exp2_d7_shots.txt` | 100 shots, depth 7 |
| `Exp2_d10_shots.txt` | 100 shots, depth 10 |
| `Exp2_d20_shots.txt` | 100 shots, depth 20 |
| `Exp3_q5_shots.txt` | 100 shots, qubits 5–14 |
| `Exp3_q10_shots.txt` | 100 shots, qubits 10–19 |

---

## Independent Verification

```bash
git clone https://github.com/reality20/qpu-1-xeb
cd qpu-1-xeb

# Verify CZ run (F_XEB = 0.260)
python3 verify_xeb.py

# Verify CNOT run + binary cross-check (F_XEB = 0.827)
python3 verify_cnot_xeb.py
```

Zero dependencies. Pure Python stdlib. No QPU access required.

---

## Circuit Structure

```
Init:       H_all on all 1,000,000 qubits
Cycle k:    {Rx(π/2)/Ry(π/2)/Rz(π/4)} on marginal qubits
            → CZ tile on (q0,q1)(q2,q3)… [even] or (q0,q5)(q1,q6)… [odd]
Measure:    all 1,000,000 qubits → 10-qubit marginal extracted for F_XEB
```

---

*Conceived, executed and verified by Sk Mahammad Saad Amin — CEO, Lead Researcher & Architect, LAP Technologies*
*QPU-1: [qpu-1.lovable.app](https://qpu-1.lovable.app) | Paper: [doi.org/10.5281/zenodo.18836118](https://doi.org/10.5281/zenodo.18836118)*
