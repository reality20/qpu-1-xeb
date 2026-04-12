"""
QPU1 Client Library
===================
Python client for interacting with lap-quantum QPU-1 MCP API.
"""

from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class QPU1Client:
    """
    Client for interacting with the lap-quantum QPU-1 MCP API.
    
    Provides methods for executing quantum circuits, creating states,
    and querying QPU health status.
    """

    def __init__(self, base_url: str = "https://lap-quantum-qpu-1-api.hf.space"):
        """
        Initialize the QPU1 client.
        
        Args:
            base_url: Base URL for the QPU-1 API (default: https://lap-quantum-qpu-1-api.hf.space)
        """
        self.base_url = base_url.rstrip("/")
        self.session = self._create_session()
        self._connected = False

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with connection pooling and retry logic.
        
        Returns:
            Configured requests.Session with HTTPAdapter and Retry
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def connect(self) -> bool:
        """
        Establish connection to the QPU-1 API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=30
            )
            self._connected = response.status_code == 200
            return self._connected
        except requests.exceptions.RequestException:
            self._connected = False
            return self._connected

    def execute_qreg(self, code: str) -> str:
        """
        Execute Qreg quantum code.
        
        Args:
            code: Qreg quantum code string
            
        Returns:
            Execution result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/execute/qreg",
            json={"code": code},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def execute_qasm(self, qasm: str) -> str:
        """
        Execute QASM code.
        
        Args:
            qasm: QASM code string
            
        Returns:
            Execution result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/execute/qasm",
            json={"qasm": qasm},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def create_circuit(self, num_qubits: int, seed: Optional[int] = None) -> str:
        """
        Create a quantum circuit.
        
        Args:
            num_qubits: Number of qubits in the circuit
            seed: Optional random seed for reproducibility
            
        Returns:
            Circuit ID as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        payload = {"num_qubits": num_qubits}
        if seed is not None:
            payload["seed"] = seed
            
        response = self.session.post(
            f"{self.base_url}/circuit/create",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("circuit_id", "")

    def apply_gate(self, circuit_id: str, gate: str, params: dict) -> str:
        """
        Apply a quantum gate to a circuit.
        
        Args:
            circuit_id: ID of the circuit to modify
            gate: Gate name (e.g., "H", "X", "Y", "Z", "CNOT", "CZ", "RX", "RY", "RZ")
            params: Gate parameters (e.g., {"qubit": 0} or {"control": 0, "target": 1})
            
        Returns:
            Operation result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/circuit/{circuit_id}/gate",
            json={"gate": gate, "params": params},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def measure_circuit(self, circuit_id: str, qubit: Optional[int] = None) -> str:
        """
        Measure the circuit.
        
        Args:
            circuit_id: ID of the circuit to measure
            qubit: Optional specific qubit to measure
            
        Returns:
            Measurement result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        payload = {"circuit_id": circuit_id}
        if qubit is not None:
            payload["qubit"] = qubit
            
        response = self.session.post(
            f"{self.base_url}/circuit/measure",
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def get_health(self) -> dict:
        """
        Get QPU health status.
        
        Returns:
            Dictionary containing health status information
            
        Raises:
            requests.exceptions.RequestException: On request failure
        """
        response = self.session.get(
            f"{self.base_url}/health",
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def create_bell_state(self) -> str:
        """
        Create a Bell state (entangled pair of qubits).
        
        Returns:
            Execution result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/state/bell",
            json={},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def create_superposition(self, num_qubits: int) -> str:
        """
        Create a superposition state on the specified number of qubits.
        
        Args:
            num_qubits: Number of qubits to put in superposition
            
        Returns:
            Execution result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/state/superposition",
            json={"num_qubits": num_qubits},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")

    def create_ghz_state(self, num_qubits: int) -> str:
        """
        Create a GHZ (Greenberger-Horne-Zeilinger) state.
        
        Args:
            num_qubits: Number of qubits in the GHZ state
            
        Returns:
            Execution result as string
            
        Raises:
            requests.exceptions.RequestException: On request failure
            ValueError: If API returns error
        """
        response = self.session.post(
            f"{self.base_url}/state/ghz",
            json={"num_qubits": num_qubits},
            timeout=300
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise ValueError(result["error"])
        return result.get("result", "")