"""
QPU1 Client Library
====================
Python client for interacting with lap-quantum QPU-1 MCP API.
"""

import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Optional


class QPU1Client:
    """Client for QPU-1 quantum computing API."""

    def __init__(self, base_url: str = "https://lap-quantum-qpu-1-api.hf.space"):
        self.base_url = base_url.rstrip("/")
        self.session = None
        self._connected = False

    def connect(self) -> None:
        """Establish connection to QPU-1 API."""
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=retry_strategy,
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self._connected = True

    def _execute(self, endpoint: str, data: dict) -> dict:
        """Execute a request to the API."""
        if not self._connected:
            self.connect()

        url = f"{self.base_url}/{endpoint}"
        response = self.session.post(url, json=data, timeout=300)
        response.raise_for_status()
        return response.json()

    def execute_qreg(self, code: str) -> str:
        """Execute Qreg quantum code."""
        return self._execute("execute_qreg", {"code": code})

    def execute_qasm(self, qasm: str) -> str:
        """Execute QASM code."""
        return self._execute("execute_qasm", {"qasm": qasm})

    def create_circuit(self, num_qubits: int, seed: Optional[int] = None) -> str:
        """Create a quantum circuit."""
        data = {"num_qubits": num_qubits}
        if seed is not None:
            data["seed"] = seed
        return self._execute("create_circuit", data)

    def apply_gate(self, circuit_id: str, gate: str, params: dict) -> str:
        """Apply a gate to a circuit."""
        return self._execute("apply_gate", {
            "circuit_id": circuit_id,
            "gate": gate,
            "params": params,
        })

    def measure_circuit(self, circuit_id: str, qubit: Optional[int] = None) -> str:
        """Measure a circuit."""
        data = {"circuit_id": circuit_id}
        if qubit is not None:
            data["qubit"] = qubit
        return self._execute("measure_circuit", data)

    def get_health(self) -> dict:
        """Get QPU health status."""
        return self._execute("health", {})

    def create_bell_state(self) -> str:
        """Create a Bell state circuit."""
        return self._execute("create_bell_state", {})

    def create_superposition(self, num_qubits: int) -> str:
        """Create a superposition state."""
        return self._execute("create_superposition", {"num_qubits": num_qubits})

    def create_ghz_state(self, num_qubits: int) -> str:
        """Create a GHZ state."""
        return self._execute("create_ghz_state", {"num_qubits": num_qubits})