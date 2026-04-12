"""
run_qv_benchmark.py - Quantum Volume Benchmark for QPU1
=========================================================
Implements standard Quantum Volume (QV) benchmarking protocol:
- generate_qv_circuit(n): Generate QV circuit for n qubits (2^n volume)
- compute_heavy_output_probability(measured_bits, ideal_probs): Compute HOP
- run_qv_test(n_start, n_end, trials): Run QV tests from n_start to n_end

Classical simulation for ideal_probs using numpy (statevector simulation).
Output: {n, vol, hops, mean_hop, threshold, passed}
Save results to qv_qpu1_results.json
"""

import json
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


API_URL = "https://lap-quantum-qpu-1-api.hf.space"


def apply_H(sv, q, n):
    s = 1.0 / math.sqrt(2)
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1 == 0:
            j = i | (1 << q)
            r[i] = s * sv[i] + s * sv[j]
            r[j] = s * sv[i] - s * sv[j]
    return r


def apply_X(sv, q, n):
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1:
            j = i & ~(1 << q)
            k = i | (1 << q)
            r[j], r[k] = sv[k], sv[j]
    return r


def apply_Y(sv, q, n):
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1:
            r[i] = complex(-sv[i].imag, sv[i].real)
    return r


def apply_Z(sv, q, n):
    r = list(sv)
    for i in range(1 << n):
        if (i >> q) & 1:
            r[i] = -r[i]
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


def apply_CNOT(sv, ctrl, target, n):
    r = list(sv)
    for i in range(1 << n):
        if (i >> ctrl) & 1:
            t = target
            if (i >> t) & 1:
                j = i & ~(1 << t)
            else:
                j = i | (1 << t)
            r[i] = sv[j]
            r[j] = sv[i]
    return r


GATES_1Q = {
    "H": apply_H,
    "X": apply_X,
    "Y": apply_Y,
    "Z": apply_Z,
    "S": apply_S,
    "T": apply_T,
}


def generate_qv_circuit(n: int, seed: int = None) -> str:
    """
    Generate QV circuit for n qubits.
    QV circuit: depth = n, random single-qubit gates + entangling layers.
    Returns Qreg script as string.
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    rng = random.Random(seed)

    depth = n

    script = f"""
import random
import time

N = {n}
DEPTH = {depth}
SEED = {seed}

rng = random.Random(SEED)

q = Qreg(N)
q.reset_all()

single_gates = ["H", "X", "Y", "Z", "S", "T"]

for d in range(DEPTH):
    for i in range(N):
        gate = rng.choice(single_gates)
        if gate == "H":
            q.H(i)
        elif gate == "X":
            q.X(i)
        elif gate == "Y":
            q.Y(i)
        elif gate == "Z":
            q.Z(i)
        elif gate == "S":
            q.S(i)
        elif gate == "T":
            q.T(i)
    
    if d % 2 == 0:
        for i in range(0, N - 1, 2):
            q.CZ(i, i + 1)
    else:
        for i in range(1, N - 1, 2):
            q.CZ(i, i + 1)

bits = q.measure()
bits_str = "".join(str(int(b)) for b in bits)
print("MEASURED:" + bits_str)
print("DONE")
"""
    return script


def simulate_qv_circuit(n: int, seed: int = None) -> dict:
    """
    Classical simulation of QV circuit using numpy statevector.
    Returns ideal_probs dict: {bitstring: probability}
    """
    if seed is None:
        seed = seed or random.randint(0, 2**31 - 1)
    rng = random.Random(seed)

    depth = n

    dim = 1 << n
    amp = 1.0 / math.sqrt(dim)
    sv = [complex(amp)] * dim

    for d in range(depth):
        for q in range(n):
            gate = rng.choice(["H", "X", "Y", "Z", "S", "T"])
            sv = GATES_1Q[gate](sv, q, n)

        if d % 2 == 0:
            for i in range(0, n - 1, 2):
                sv = apply_CZ(sv, i, i + 1, n)
        else:
            for i in range(1, n - 1, 2):
                sv = apply_CZ(sv, i, i + 1, n)

    ideal_probs = {format(i, f"0{n}b"): abs(sv[i]) ** 2 for i in range(dim)}
    return ideal_probs


def compute_heavy_output_probability(measured_bits: list, ideal_probs: dict) -> float:
    """
    Compute Heavy Output Probability (HOP).
    Heavy outputs are bitstrings with probability > median (excluding median).
    """
    probs = list(ideal_probs.values())
    probs.sort()

    if len(probs) % 2 == 0:
        median = (probs[len(probs) // 2 - 1] + probs[len(probs) // 2]) / 2
    else:
        median = probs[len(probs) // 2]

    heavy_probs = [p for p in probs if p > median]

    if not measured_bits:
        return 0.0

    heavy_count = 0
    for bits in measured_bits:
        prob = ideal_probs.get(bits, 0.0)
        if prob > median:
            heavy_count += 1

    return heavy_count / len(measured_bits)


def execute_on_qpu(script: str, timeout: int = 300) -> str:
    """
    Execute Qreg script on QPU-1 API.
    """
    import requests
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
    session.mount("https://", adapter)

    try:
        response = session.post(
            f"{API_URL}/execute-qreg",
            json={"code": script},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"QPU execution error: {e}")
        return ""


def run_qv_test(n_start: int, n_end: int, trials: int = 100) -> dict:
    """
    Run QV tests from n_start to n_end qubits.
    Each n runs 'trials' number of circuits.
    Output: {n: int, vol: int, hops: list, mean_hop: float, threshold: float, passed: bool}
    """
    results = []

    for n in range(n_start, n_end + 1):
        vol = 2 ** n
        threshold = 2.0 / 3.0

        hops = []
        print(f"\n=== Testing n={n}, vol={vol} ===")

        for trial in range(trials):
            seed = n * 1000 + trial

            script = generate_qv_circuit(n, seed)
            ideal_probs = simulate_qv_circuit(n, seed)

            result = execute_on_qpu(script)

            measured_bits = None
            for line in result.splitlines():
                if line.startswith("MEASURED:"):
                    measured_bits = line.split(":", 1)[1].strip()
                    break

            if measured_bits:
                hop = compute_heavy_output_probability([measured_bits], ideal_probs)
                hops.append(hop)
                print(f"  Trial {trial + 1}/{trials}: HOP = {hop:.4f}")
            else:
                print(f"  Trial {trial + 1}/{trials}: FAILED")

        mean_hop = sum(hops) / len(hops) if hops else 0.0
        passed = mean_hop > threshold

        result_entry = {
            "n": n,
            "vol": vol,
            "hops": hops,
            "mean_hop": mean_hop,
            "threshold": threshold,
            "passed": passed,
        }
        results.append(result_entry)

        print(f"n={n}: mean_hop={mean_hop:.4f}, threshold={threshold}, passed={passed}")

    return {"results": results}


def save_results(results: dict, output_path: str):
    """Save results to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output = {}
    for r in results.get("results", []):
        n = r["n"]
        output[n] = {
            "n": r["n"],
            "vol": r["vol"],
            "hops": r["hops"],
            "mean_hop": r["mean_hop"],
            "threshold": r["threshold"],
            "passed": r["passed"],
        }

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qv")
    os.makedirs(OUT_DIR, exist_ok=True)
    OUTPUT_FILE = os.path.join(OUT_DIR, "qv_qpu1_results.json")

    print("Starting QV Benchmark for QPU1")
    print("=" * 50)

    results = run_qv_test(n_start=3, n_end=6, trials=10)

    save_results(results, OUTPUT_FILE)
    print(f"\nResults saved to {OUTPUT_FILE}")
