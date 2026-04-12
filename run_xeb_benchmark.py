"""
run_xeb_benchmark.py — XEB (Cross-Entropy Benchmarking) on QPU1
================================================================
Run XEB benchmarks on the quantum processor.
"""

import json
import math
import random
import time
from typing import List, Dict, Optional

from browse.qpu1_client import QPU1Client


def generate_random_circuit(num_qubits: int, depth: int, seed: int) -> Dict:
    """
    Generate random Qreg circuit for XEB benchmarking.
    
    Returns a dict with:
        - circuit_seed: int
        - circuit_depth: int  
        - marginal_n: int (num_qubits for simulation)
        - gate_sequence: list of lists of gate names
        - cz_even: list of [control, target] pairs for even cycles
        - cz_odd: list of [control, target] pairs for odd cycles
    """
    random.seed(seed)
    
    gate_set = ["H", "S", "T"]
    gate_sequence = []
    
    for _ in range(depth):
        cycle_gates = [random.choice(gate_set) for _ in range(num_qubits)]
        gate_sequence.append(cycle_gates)
    
    cz_even = [[i, i + 1] for i in range(0, num_qubits - 1, 2)]
    cz_odd = [[i, i + 5] for i in range(0, num_qubits - 5, 1)]
    cz_odd = [pair for pair in cz_odd if pair[1] < num_qubits]
    
    return {
        "circuit_seed": seed,
        "circuit_depth": depth,
        "marginal_n": num_qubits,
        "gate_sequence": gate_sequence,
        "cz_even": cz_even,
        "cz_odd": cz_odd,
    }


def circuit_to_qreg_code(circuit: Dict) -> str:
    """Convert circuit dict to Qreg code string."""
    num_qubits = circuit["marginal_n"]
    depth = circuit["circuit_depth"]
    gate_sequence = circuit["gate_sequence"]
    cz_even = circuit["cz_even"]
    cz_odd = circuit["cz_odd"]
    
    lines = [f"qreg q[{num_qubits}];"]
    
    for q in range(num_qubits):
        lines.append(f"H q[{q}];")
    
    for cycle in range(depth):
        for q, gate in enumerate(gate_sequence[cycle]):
            if gate == "H":
                lines.append(f"H q[{q}];")
            elif gate == "S":
                lines.append(f"S q[{q}];")
            elif gate == "T":
                lines.append(f"T q[{q}];")
        
        pairs = cz_even if cycle % 2 == 0 else cz_odd
        for ctrl, tgt in pairs:
            if ctrl < num_qubits and tgt < num_qubits:
                lines.append(f" CZ q[{ctrl}], q[{tgt}];")
    
    return "\n".join(lines)


def simulate_circuit_classically(circuit: Dict) -> Dict[str, float]:
    """Classically simulate the circuit to get ideal probabilities."""
    n = circuit["marginal_n"]
    depth = circuit["circuit_depth"]
    gate_sequence = circuit["gate_sequence"]
    cz_even = circuit["cz_even"]
    cz_odd = circuit["cz_odd"]
    
    def apply_H(sv, q):
        s = 1.0 / math.sqrt(2)
        r = list(sv)
        for i in range(1 << n):
            if (i >> q) & 1 == 0:
                j = i | (1 << q)
                r[i] = s * sv[i] + s * sv[j]
                r[j] = s * sv[i] - s * sv[j]
        return r

    def apply_S(sv, q):
        r = list(sv)
        for i in range(1 << n):
            if (i >> q) & 1:
                r[i] = sv[i] * complex(0, 1)
        return r

    def apply_T(sv, q):
        r = list(sv)
        ang = math.pi / 4
        phase = complex(math.cos(ang), math.sin(ang))
        for i in range(1 << n):
            if (i >> q) & 1:
                r[i] = sv[i] * phase
        return r

    def apply_CZ(sv, q0, q1):
        r = list(sv)
        for i in range(1 << n):
            if ((i >> q0) & 1) and ((i >> q1) & 1):
                r[i] = -r[i]
        return r

    GATE_FN = {"H": apply_H, "S": apply_S, "T": apply_T}
    
    dim = 1 << n
    amp = 1.0 / math.sqrt(dim)
    sv = [complex(amp)] * dim
    
    for cycle in range(depth):
        for qi, gate in enumerate(gate_sequence[cycle]):
            sv = GATE_FN[gate](sv, qi)
        pairs = cz_even if cycle % 2 == 0 else cz_odd
        for q0, q1 in pairs:
            if q0 < n and q1 < n:
                sv = apply_CZ(sv, q0, q1)
    
    ideal_probs = {format(i, f"0{n}b"): abs(sv[i])**2 for i in range(dim)}
    return ideal_probs


def execute_circuit_on_qpu1(circuit: Dict, client: QPU1Client) -> List[str]:
    """Execute circuit on QPU1 and return measurement shots."""
    qreg_code = circuit_to_qreg_code(circuit)
    
    result = client.execute_qreg(qreg_code)
    
    if isinstance(result, dict) and "shots" in result:
        return result["shots"]
    elif isinstance(result, list):
        return result
    else:
        raise ValueError(f"Unexpected result format: {result}")


def compute_f_xeb(shots: List[str], ideal_probs: Dict[str, float]) -> float:
    """Compute F_XEB fidelity from shots and ideal probabilities."""
    if not shots:
        return 0.0
    
    D = len(ideal_probs)
    probs_measured = [ideal_probs.get(s, 0.0) for s in shots]
    mean_p = sum(probs_measured) / len(shots)
    F_xeb = D * mean_p - 1.0
    
    return F_xeb


def run_xeb_sweep(
    num_qubits_range: List[int],
    depth_range: List[int],
    shots: int,
    client: QPU1Client,
) -> Dict:
    """Run XEB benchmarks across parameter sweep."""
    results = []
    all_shots = []
    
    seed_base = int(time.time())
    
    for n_qubits in num_qubits_range:
        for depth in depth_range:
            seed = seed_base + n_qubits * 100 + depth
            print(f"Running XEB: n_qubits={n_qubits}, depth={depth}, seed={seed}")
            
            circuit = generate_random_circuit(n_qubits, depth, seed)
            
            ideal_probs = simulate_circuit_classically(circuit)
            
            try:
                qpu_shots = execute_circuit_on_qpu1(circuit, client)
                
                if len(qpu_shots) > shots:
                    qpu_shots = qpu_shots[:shots]
                
                f_xeb = compute_f_xeb(qpu_shots, ideal_probs)
                
                result = {
                    "circuit_seed": circuit["circuit_seed"],
                    "circuit_depth": circuit["circuit_depth"],
                    "marginal_n": circuit["marginal_n"],
                    "gate_sequence": circuit["gate_sequence"],
                    "cz_even": circuit["cz_even"],
                    "cz_odd": circuit["cz_odd"],
                    "n_shots": len(qpu_shots),
                    "D": 2 ** n_qubits,
                    "F_XEB": f_xeb,
                }
                results.append(result)
                all_shots.extend(qpu_shots)
                
                print(f"  F_XEB = {f_xeb:.4f}")
                
            except Exception as e:
                print(f"  Error: {e}")
                continue
    
    return {
        "results": results,
        "shots": all_shots,
    }


def main():
    """Run XEB benchmark on QPU1."""
    print("Connecting to QPU1...")
    client = QPU1Client()
    client.connect()
    
    print("Running XEB sweep...")
    sweep_results = run_xeb_sweep(
        num_qubits_range=[4, 6, 8],
        depth_range=[4, 6, 8],
        shots=100,
        client=client,
    )
    
    results = sweep_results["results"]
    shots = sweep_results["shots"]
    
    output_results = []
    for r in results:
        output_results.append({
            "circuit_seed": r["circuit_seed"],
            "circuit_depth": r["circuit_depth"],
            "marginal_n": r["marginal_n"],
            "gate_sequence": r["gate_sequence"],
            "cz_even": r["cz_even"],
            "cz_odd": r["cz_odd"],
            "n_shots": r["n_shots"],
            "D": r["D"],
            "F_XEB": r["F_XEB"],
        })
    
    with open("xeb_qpu1_results.json", "w") as f:
        json.dump(output_results, f, indent=2)
    
    with open("xeb_qpu1_shots.txt", "w") as f:
        for shot in shots:
            f.write(f"{shot}\n")
    
    print(f"Results saved to xeb_qpu1_results.json ({len(results)} circuits)")
    print(f"Shots saved to xeb_qpu1_shots.txt ({len(shots)} shots)")


if __name__ == "__main__":
    main()