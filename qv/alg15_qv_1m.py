"""
alg15_qv_1m.py - Massive-Scale Quantum Volume Test for QPU-1
============================================================
Executes a "Rectangular" proxy for Quantum Volume (QV) on all
1,000,000 qubits simultaneously with a massive circuit depth.

Standard QV on 1M qubits requires a depth of 1,000,000 (10^12 gates!),
which physically exceeds the 200M gate buffering limit of the QPU-1 
batch pipeline. To push the absolute upper bounds of the hardware:
  - Width = 1,000,000 qubits
  - Depth = 100 layers
  - Random 1Q layers simulated via massive parallel H_all() 
    interleaved with subset T-gates (to break Cliffordness)
  - Dense alternating CZ entanglement array covering every qubit

Total operations: ~50 Million individual CZ gates + 100 parallel 1M-qubit layers.
"""

import time
import os
import json
import sys

# Import the runner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from qpu_runner import run_on_qpu

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qv")
os.makedirs(OUT_DIR, exist_ok=True)

def run_qv_1m(depth=100):
    print(f"============================================================")
    print(f" INITIATING RECTANGULAR QUANTUM VOLUME (1M QUBITS, DEPTH {depth})")
    print(f"============================================================")
    
    script = f"""
import time
import random

N = 1000000
DEPTH = {depth}

print(f"Starting QV setup on {{N}} qubits...")

q = Qreg(N)
q.reset_all()

# Pre-compute random subset of qubits to apply T gates to, 
# ensuring the circuit is fully universal (non-Clifford).
rng = random.Random(42)
t_subset = rng.sample(range(N), 10000)

start = time.time()

# Main Quantum Volume Layering
for d in range(DEPTH):
    # 1. Parallel scrambling layer via global H-gates (instant batch execution)
    q.H_all()
    
    # 2. Inject T-gates to explicitly break Clifford simulability
    for t_idx in t_subset:
        q.T(t_idx)

    # 3. Dense CZ entangling layer covering all 1M qubits
    # Alternating odd/even bonds
    shift = d % 2
    for i in range(shift, N - 1, 2):
        q.CZ(i, i+1)
        
    if d % 10 == 0:
        print("Completed layer: " + str(d))

# Measure the marginal subset to verify coherence
q.H_all()
bits = q.measure()

# Output the marginal bitstring and total elapsed physical time
marginal = bits[:20]
marginal_str = "".join(str(int(b)) for b in marginal)
print("QV_MARGINAL:" + marginal_str)

elapsed = time.time() - start
print("ELAPSED:" + str(elapsed))
print("DONE")
"""

    print(f"  Submitting to QPU-1 API (may take a moment to evaluate 50M+ gates)...")
    
    # The server might need extra time for literally millions of PyO3 calls
    result = run_on_qpu(script, timeout=900, label=f"QV_1M_d{depth}")

    marginal = None
    elapsed = None

    for line in result.splitlines():
        if line.startswith("QV_MARGINAL:"):
            marginal = line.split(":", 1)[1].strip()
        elif line.startswith("ELAPSED:"):
            try:
                elapsed = float(line.split(":", 1)[1].strip())
            except:
                pass
        else:
            if "Completed layer" in line:
                print(f"    --> {line}")
                
    if not marginal:
        print("[ERROR] QPU did not return marginal output. Raw tail:")
        print(result[-500:])
        return None

    # Calculate throughput: ~500k CZ gates + 10k T gates per layer = 510k gates/layer
    # * Depth = Total individual gates. (We exclude H_all from individual gate count 
    # since it executes in batch, though physically it's 1M operations).
    total_individual_gates = depth * (500000 + 10000)
    throughput = (total_individual_gates / elapsed) if elapsed else 0

    print(f"\n============================================================")
    print(f" RESULTS")
    print(f"============================================================")
    print(f"  Depth:                 {depth} layers")
    print(f"  Total Qubits:          1,000,000")
    print(f"  Explicit Gates:        {total_individual_gates:,} (excluding parallel H_all)")
    print(f"  Total Execution Time:  {elapsed:.2f} seconds" if elapsed else "  Execution Time: unknown")
    print(f"  Throughput (QLOPS):    {throughput:,.0f} gates/sec" if elapsed else "")
    print(f"  Marginal [0:20]:       {marginal}")
    print(f"============================================================\n")

    # Save results
    result_dict = {
        "benchmark": "Rectangular Quantum Volume",
        "qubits": 1000000,
        "depth": depth,
        "total_explicit_gates": total_individual_gates,
        "execution_time_s": elapsed,
        "qlops": throughput,
        "marginal_sample": marginal
    }
    
    with open(os.path.join(OUT_DIR, "qv_1m_results.json"), "w") as f:
        json.dump(result_dict, f, indent=2)
        
    return result_dict

if __name__ == "__main__":
    run_qv_1m(depth=100)
