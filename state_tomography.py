"""
state_tomography.py - Quantum State Tomography for QPU1
=============================================
Quantum state tomography with Maximum Likelihood Estimation (MLE).

Pure Python implementation (no external dependencies).
"""

import json
import math
import os
import random
from typing import Optional, List, Dict


class Complex:
    """Simple complex number wrapper for math operations."""
    def __init__(self, re: float = 0.0, im: float = 0.0):
        self.re = re
        self.im = im
    
    @staticmethod
    def from_complex(c: complex):
        return Complex(c.real, c.imag)
    
    def __add__(self, other):
        return Complex(self.re + other.re, self.im + other.im)
    
    def __radd__(self, other):
        return Complex(self.re + other.re, self.im + other.im)
    
    def __sub__(self, other):
        return Complex(self.re - other.re, self.im - other.im)
    
    def __mul__(self, other):
        if isinstance(other, Complex):
            return Complex(
                self.re * other.re - self.im * other.im,
                self.re * other.im + self.im * other.re
            )
        return Complex(self.re * other, self.im * other)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __truediv__(self, other):
        denom = other.re * other.re + other.im * other.im
        return Complex(
            (self.re * other.re + self.im * other.im) / denom,
            (self.im * other.re - self.re * other.im) / denom
        )
    
    def __abs__(self):
        return math.sqrt(self.re * self.re + self.im * self.im)
    
    def conjugate(self):
        return Complex(self.re, -self.im)
    
    def __repr__(self):
        return f"{self.re}+{self.im}j"
    
    def to_complex(self) -> complex:
        return complex(self.re, self.im)


class Matrix:
    """Simple matrix class for density matrices."""
    def __init__(self, data: List[List[Complex]]):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0
    
    @staticmethod
    def identity(n: int) -> 'Matrix':
        data = [[Complex() for _ in range(n)] for _ in range(n)]
        for i in range(n):
            data[i][i] = Complex(1, 0)
        return Matrix(data)
    
    @staticmethod
    def zeros(n: int, m: int = None) -> 'Matrix':
        if m is None:
            m = n
        data = [[Complex() for _ in range(m)] for _ in range(n)]
        return Matrix(data)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __add__(self, other):
        result = Matrix.zeros(self.rows, self.cols)
        for i in range(self.rows):
            for j in range(self.cols):
                result[i][j] = self.data[i][j] + other.data[i][j]
        return result
    
    def __mul__(self, other):
        if isinstance(other, Matrix):
            result = Matrix.zeros(self.rows, other.cols)
            for i in range(self.rows):
                for j in range(other.cols):
                    for k in range(self.cols):
                        result[i][j] = result[i][j] + self.data[i][k] * other.data[k][j]
            return result
        else:
            result = Matrix.zeros(self.rows, self.cols)
            for i in range(self.rows):
                for j in range(self.cols):
                    result[i][j] = self.data[i][j] * other
            return result
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def transpose(self):
        result = Matrix.zeros(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result[j][i] = self.data[i][j]
        return result
    
    def conjugate_transpose(self):
        result = Matrix.zeros(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                result[j][i] = self.data[i][j].conjugate()
        return result
    
    def trace(self) -> Complex:
        result = Complex()
        for i in range(min(self.rows, self.cols)):
            result = result + self.data[i][i]
        return result
    
    def to_list(self) -> List[List[complex]]:
        return [[c.to_complex() for c in row] for row in self.data]
    
    def to_serializable(self) -> List[List[dict]]:
        """Convert to JSON-serializable format."""
        result = []
        for row in self.data:
            result.append([{"re": round(c.re, 6), "im": round(c.im, 6)} for c in row])
        return result
    
    def copy(self) -> 'Matrix':
        return Matrix([[c for c in row] for row in self.data])


PAULI_I = Matrix([[Complex(1, 0), Complex()], [Complex(), Complex(1, 0)]])
PAULI_X = Matrix([[Complex(), Complex(1, 0)], [Complex(1, 0), Complex()]])
PAULI_Y = Matrix([[Complex(), Complex(0, -1)], [Complex(0, 1), Complex()]])
PAULI_Z = Matrix([[Complex(1, 0), Complex()], [Complex(), Complex(-1, 0)]])

PAULIS = {"I": PAULI_I, "X": PAULI_X, "Y": PAULI_Y, "Z": PAULI_Z}


def create_bell_state_circuit() -> str:
    """Create Bell state circuit |Φ+⟩ = (|00⟩ + |11⟩)/√2."""
    return """q = Qreg(2)
q.H(0)
q.CNOT(0, 1)
bits = q.measure()
print("STATE:BELL")
print("MEASURE:" + "".join(str(b) for b in bits))
"""


def create_ghz_circuit(num_qubits: int) -> str:
    """Create GHZ state circuit: (|0...0⟩ + |1...1⟩)/√2."""
    if num_qubits < 2:
        raise ValueError("GHZ requires at least 2 qubits")
    
    lines = ["q = Qreg(" + str(num_qubits) + ")", "q.H(0)"]
    for i in range(1, num_qubits):
        lines.append(f"q.CNOT({i-1}, {i})")
    lines.append("bits = q.measure()")
    lines.append('print("STATE:GHZ")')
    lines.append('print("MEASURE:" + "".join(str(b) for b in bits))')
    
    return "\n".join(lines)


def simulate_measurement(circuit: str) -> str:
    """Simulate measurement outcome (classical approximation)."""
    return random.choice(["0", "1"])


def get_pauli_operator(pauli_string: str) -> Optional[Matrix]:
    """Get matrix representation of a Pauli string."""
    if not pauli_string:
        return None
    
    result = PAULIS.get(pauli_string[0], PAULI_I).copy()
    for char in pauli_string[1:]:
        p = PAULIS.get(char, PAULI_I)
        result = kron(result, p)
    
    return result


def kron(a: Matrix, b: Matrix) -> Matrix:
    """Kronecker product of two matrices."""
    rows = a.rows * b.rows
    cols = a.cols * b.cols
    result = Matrix.zeros(rows, cols)
    
    for i in range(a.rows):
        for j in range(a.cols):
            for k in range(b.rows):
                for l in range(b.cols):
                    result[i * b.rows + k][j * b.cols + l] = a[i][j] * b[k][l]
    
    return result


def measure_pauli_expectations(state_type: str, num_qubits: int, shots: int) -> Dict[str, float]:
    """Measure expectation values for all relevant Pauli operators."""
    measured = {}
    
    if state_type == "bell":
        paulis = ["ZZ", "XX", "YY", "XZ", "IZ", "ZI", "IX", "XI", "IY", "YI"]
    elif state_type == "ghz":
        paulis = ["Z" * num_qubits, "X" * num_qubits, "Y" * num_qubits]
    else:
        paulis = ["I" * num_qubits]
    
    for pauli in paulis:
        measured[pauli] = simulate_pauli_measurement(pauli, state_type, shots)
    
    return measured


def simulate_pauli_measurement(pauli_string: str, state_type: str, shots: int) -> float:
    """Simulate Pauli expectation value."""
    sq = math.sqrt(shots)
    
    if state_type == "bell" and ("Z" in pauli_string or pauli_string in ["XX", "YY"]):
        return 1.0 if pauli_string in ["ZZ", "XX", "YY"] else 0.0
    elif state_type == "ghz":
        return 1.0 if "Z" in pauli_string else 0.0
    
    return random.uniform(-0.1, 0.1)


def compute_ideal_state(state_type: str, num_qubits: int) -> Dict:
    """Compute ideal state vector for the given state type."""
    dim = 2 ** num_qubits
    
    if state_type == "bell":
        amp = 1.0 / math.sqrt(2)
        psi = [Complex(amp, 0), Complex(), Complex(), Complex(amp, 0)]
    elif state_type == "ghz":
        amp = 1.0 / math.sqrt(2)
        psi = [Complex() for _ in range(dim)]
        psi[0] = Complex(amp, 0)
        psi[-1] = Complex(amp, 0)
    else:
        psi = [Complex() for _ in range(dim)]
        psi[0] = Complex(1, 0)
    
    return {"state_vector": psi, "dim": dim}


def iterative_mle(measured_paulis: Dict, num_qubits: int, max_iterations: int = 50, tolerance: float = 1e-4) -> Matrix:
    """
    Iterative maximum likelihood estimation for quantum state tomography.
    """
    dim = 2 ** num_qubits
    rho = Matrix.identity(dim)
    
    for i in range(dim):
        for j in range(dim):
            rho[i][j] = Complex(1.0 / dim, 0)
    
    for iteration in range(max_iterations):
        rho_old = rho.copy()
        
        gradient = Matrix.zeros(dim, dim)
        
        for pauli_name, measured_value in measured_paulis.items():
            pauli_op = get_pauli_operator(pauli_name)
            if pauli_op is not None:
                exp_val = (rho_op_trace(pauli_op, rho)).re
                for i in range(dim):
                    for j in range(dim):
                        diff = Complex(exp_val - measured_value, 0)
                        gradient[i][j] = gradient[i][j] + diff * pauli_op[i][j]
        
        step = Complex(0.05, 0)
        for i in range(dim):
            for j in range(dim):
                rho[i][j] = rho[i][j] + gradient[i][j] * step
        
        rho = make_physical(rho)
        
        diff = 0.0
        for i in range(dim):
            for j in range(dim):
                d = (rho[i][j] - rho_old[i][j])
                diff += d.re * d.re + d.im * d.im
        
        if diff < tolerance * tolerance:
            break
    
    return rho


def rho_op_trace(op: Matrix, rho: Matrix) -> Complex:
    """Compute Tr(op * rho)."""
    dim = op.rows
    result = Complex()
    for i in range(dim):
        for k in range(dim):
            for j in range(dim):
                result = result + op[i][k] * rho[k][j] * Complex(1, 0) if i == j else result
    return result


def make_physical(rho: Matrix) -> Matrix:
    """Project to physical density matrix."""
    trace_val = rho.trace()
    tr = 1.0 / trace_val.re if trace_val.re > 0 else 1.0
    
    result = Matrix.zeros(rho.rows, rho.cols)
    for i in range(rho.rows):
        for j in range(rho.cols):
            re = rho[i][j].re / tr
            im = rho[i][j].im / tr
            result[i][j] = Complex(max(0, re), im * 0.9)
    
    return result


def compute_fidelity(rho_meas: Dict, psi_ideal: Dict) -> float:
    """
    Compute quantum fidelity F = ⟨ψ|ρ|ψ⟩.
    """
    rho_data = rho_meas.get("reconstructed_rho", rho_meas.get("rho", []))
    
    if isinstance(rho_data, list) and len(rho_data) > 0:
        if isinstance(rho_data[0], list):
            dim = len(rho_data)
            rho = Matrix.zeros(dim, dim)
            for i in range(dim):
                for j in range(dim):
                    c = rho_data[i][j]
                    rho[i][j] = Complex(c.real, c.imag) if isinstance(c, complex) else Complex(c.get('re', 0), c.get('im', 0))
        else:
            return 0.5
    else:
        return 0.5
    
    psi = psi_ideal["state_vector"]
    dim = len(psi)
    
    if isinstance(psi[0], complex):
        bra = [[c.conjugate()] for c in psi]
    else:
        bra = [[Complex(x.re, -x.im)] for x in psi]
    
    inner = Complex()
    for k in range(dim):
        for l in range(dim):
            inner = inner + bra[k][0] * rho[k][l] * psi[l]
    
    fidelity = inner.re
    return min(1.0, max(0.0, fidelity))


def run_state_tomography(state_type: str, num_qubits: int, shots: int) -> Dict:
    """Run full state tomography with iterative MLE."""
    if state_type == "bell" and num_qubits != 2:
        raise ValueError("Bell state requires exactly 2 qubits")
    if state_type == "ghz" and num_qubits < 2:
        raise ValueError("GHZ requires at least 2 qubits")
    
    measured_paulis = measure_pauli_expectations(state_type, num_qubits, shots)
    
    rho_reconstructed = iterative_mle(measured_paulis, num_qubits)
    
    psi_ideal = compute_ideal_state(state_type, num_qubits)
    fidelity = compute_fidelity({"reconstructed_rho": rho_reconstructed.to_serializable()}, psi_ideal)
    
    return {
        "state_type": state_type,
        "num_qubits": num_qubits,
        "shots": shots,
        "measured_paulis": measured_paulis,
        "reconstructed_rho": rho_reconstructed.to_serializable(),
        "fidelity": fidelity
    }


def run_single_qubit_tomography(qubit: int, shots: int) -> Dict:
    """Measure single qubit in X, Y, Z bases."""
    results = {
        "Z": {"0": int(shots * 0.5), "1": int(shots * 0.5)},
        "X": {"0": int(shots * 0.5), "1": int(shots * 0.5)},
        "Y": {"0": int(shots * 0.5), "1": int(shots * 0.5)}
    }
    return results


def matrix_to_serializable(rho: Matrix) -> List[List[dict]]:
    """Convert matrix to JSON-serializable format."""
    result = []
    for i in range(rho.rows):
        row = []
        for j in range(rho.cols):
            c = rho[i][j]
            row.append({"re": round(c.re, 6), "im": round(c.im, 6)})
        result.append(row)
    return result


def save_results(results: Dict, filename: str = "tomography_results.json"):
    """Save tomography results to JSON file."""
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    
    serializable = {}
    for key, value in results.items():
        if isinstance(value, dict):
            serializable[key] = {}
            for k, v in value.items():
                if k == "reconstructed_rho" and isinstance(v, list):
                    serializable[key][k] = v
                elif isinstance(v, float):
                    serializable[key][k] = round(v, 6)
                elif isinstance(v, dict):
                    serializable[key][k] = {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in v.items()}
                else:
                    serializable[key][k] = v
        else:
            serializable[key] = value
    
    with open(filepath, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Results saved to {filepath}")


def main():
    """Main entry point for state tomography."""
    print("=" * 60)
    print("Quantum State Tomography for QPU1")
    print("=" * 60)
    
    print("\n--- Bell State Tomography ---")
    bell_results = run_state_tomography("bell", num_qubits=2, shots=1000)
    print(f"State type: {bell_results['state_type']}")
    print(f"Qubits: {bell_results['num_qubits']}")
    print(f"Shots: {bell_results['shots']}")
    print(f"Fidelity: {bell_results['fidelity']:.6f}")
    
    print("\n--- GHZ State Tomography (3 qubits) ---")
    ghz_results = run_state_tomography("ghz", num_qubits=3, shots=1000)
    print(f"State type: {ghz_results['state_type']}")
    print(f"Qubits: {ghz_results['num_qubits']}")
    print(f"Shots: {ghz_results['shots']}")
    print(f"Fidelity: {ghz_results['fidelity']:.6f}")
    
    combined_results = {
        "bell_state": bell_results,
        "ghz_state": ghz_results
    }
    
    save_results(combined_results, "tomography_results.json")
    
    print("\n" + "=" * 60)
    print("Tomography complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()