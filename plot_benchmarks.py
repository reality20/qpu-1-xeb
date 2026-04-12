import json
import os
from collections import Counter
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np


def plot_xeb_fidelity(data_file: str, output: str) -> None:
    """Plot F_XEB vs depth/qubits."""
    plt.style.use('ggplot')
    
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    depth = data.get('circuit_depth', 0)
    n_qubits = data.get('marginal_n', 0)
    f_xeb = data.get('F_XEB', 0)
    verdict = data.get('verdict', '')
    
    axes[0].bar(['F_XEB'], [f_xeb], color='steelblue', edgecolor='black')
    axes[0].set_ylabel('F_XEB')
    axes[0].set_title(f'Cross-Entropy Benchmarking Fidelity\n(depth={depth}, n={n_qubits})')
    axes[0].set_ylim(0, 1)
    axes[0].axhline(y=0.5, color='red', linestyle='--', label='Classical limit (0.5)')
    axes[0].legend()
    
    verdicts = {'QUANTUM_ADVANTAGE_CONFIRMED': 'Quantum Advantage', 'FAILED': 'Failed'}
    color = 'green' if f_xeb > 0.5 else 'red'
    axes[1].text(0.5, 0.5, f'{f_xeb:.4f}', fontsize=36, ha='center', va='center', color=color)
    axes[1].text(0.5, 0.3, verdict.replace('_', ' '), fontsize=12, ha='center', va='center')
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].axis('off')
    axes[1].set_title('Verdict')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()


def plot_qv_results(qv_file: str, output: str) -> None:
    """Plot Quantum Volume results."""
    plt.style.use('ggplot')
    
    with open(qv_file, 'r') as f:
        data = json.load(f)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    n = data.get('n', 0)
    vol = data.get('vol', 0)
    hops = data.get('hops', [])
    mean_hop = data.get('mean_hop', 0)
    threshold = data.get('threshold', 0)
    passed = data.get('passed', False)
    
    if hops:
        axes[0].hist(hops, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
        axes[0].axvline(x=mean_hop, color='red', linestyle='-', linewidth=2, label=f'Mean HOP: {mean_hop:.4f}')
        axes[0].axvline(x=threshold, color='orange', linestyle='--', linewidth=2, label=f'Threshold: {threshold:.4f}')
        axes[0].set_xlabel('Heavy Output Probability')
        axes[0].set_ylabel('Count')
        axes[0].set_title(f'QV Distribution (n={n}, Volume={vol})')
        axes[0].legend()
    else:
        axes[0].text(0.5, 0.5, 'No HOP data available', ha='center', va='center', fontsize=14)
        axes[0].set_title('QV Distribution')
    
    status = 'PASSED' if passed else 'FAILED'
    color = 'green' if passed else 'red'
    result_text = f'n = {n}\nVolume = {vol}\nMean HOP = {mean_hop:.4f}\nThreshold = {threshold:.4f}'
    axes[1].text(0.5, 0.6, result_text, fontsize=14, ha='center', va='center', transform=axes[1].transAxes)
    axes[1].text(0.5, 0.2, status, fontsize=24, ha='center', va='center', color=color, fontweight='bold')
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].axis('off')
    axes[1].set_title('Result')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()


def plot_gate_fidelities(gate_data: Dict[str, float], output: str) -> None:
    """Plot gate error rates."""
    plt.style.use('ggplot')
    
    gates = list(gate_data.keys())
    error_rates = list(gate_data.values())
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['steelblue' if e < 0.01 else 'orange' if e < 0.05 else 'red' for e in error_rates]
    bars = ax.bar(gates, error_rates, color=colors, edgecolor='black')
    
    ax.set_xlabel('Gate')
    ax.set_ylabel('Error Rate')
    ax.set_title('Gate Fidelities (Error Rates)')
    ax.axhline(y=0.01, color='blue', linestyle='--', alpha=0.7, label='1% threshold')
    ax.axhline(y=0.05, color='orange', linestyle='--', alpha=0.7, label='5% threshold')
    ax.legend()
    
    for bar, err in zip(bars, error_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
               f'{err:.4f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()


def plot_correlations(shot_files: List[str], output: str) -> None:
    """Plot measurement correlations from shot files."""
    plt.style.use('ggplot')
    
    all_shots = []
    for shot_file in shot_files:
        if not os.path.exists(shot_file):
            continue
        with open(shot_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    all_shots.append(line)
    
    if not all_shots:
        print(f"No shot data found in {shot_files}")
        return
    
    num_qubits = len(all_shots[0])
    shot_counts = [len(all_shots)]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    bit_counts = [Counter() for _ in range(num_qubits)]
    for shot in all_shots:
        for i, bit in enumerate(shot):
            bit_counts[i][bit] += 1
    
    qubit_indices = list(range(num_qubits))
    prob_zeros = [bit_counts[i].get('0', 0) / shot_counts[0] for i in range(num_qubits)]
    prob_ones = [bit_counts[i].get('1', 0) / shot_counts[0] for i in range(num_qubits)]
    
    axes[0].bar(qubit_indices, prob_zeros, label='0', alpha=0.7)
    axes[0].bar(qubit_indices, prob_ones, bottom=prob_zeros, label='1', alpha=0.7)
    axes[0].set_xlabel('Qubit Index')
    axes[0].set_ylabel('Probability')
    axes[0].set_title('Bit Frequencies by Qubit')
    axes[0].legend()
    
    marginal_probs = [0.5 for _ in range(num_qubits)]
    deviation = [abs(p - 0.5) for p in prob_zeros]
    axes[1].bar(qubit_indices, deviation, color='steelblue', edgecolor='black')
    axes[1].set_xlabel('Qubit Index')
    axes[1].set_ylabel('|P(0) - 0.5|')
    axes[1].set_title('Deviation from Uniform')
    axes[1].axhline(y=0.1, color='red', linestyle='--', label='10% threshold')
    axes[1].legend()
    
    pair_counts = Counter()
    for shot in all_shots:
        for i in range(num_qubits - 1):
            pair = (shot[i], shot[i + 1])
            pair_counts[pair] += 1
    
    pair_labels = ['00', '01', '10', '11']
    pair_values = [pair_counts.get((l[0], l[1]), 0) / len(all_shots) for l in pair_labels]
    
    axes[2].bar(pair_labels, pair_values, color='steelblue', edgecolor='black')
    axes[2].set_xlabel('Bit Pair')
    axes[2].set_ylabel('Probability')
    axes[2].set_title('Pairwise Correlations')
    axes[2].axhline(y=0.25, color='red', linestyle='--', label='Uniform (0.25)')
    axes[2].legend()
    
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    """Generate all benchmark plots."""
    os.makedirs('benchmark_plots', exist_ok=True)
    
    plot_xeb_fidelity('xeb_results.json', 'benchmark_plots/xeb_fidelity.png')
    plot_qv_results('qv_qpu1_results.json', 'benchmark_plots/qv_results.png')
    
    gate_data = {
        'H': 0.001,
        'X': 0.002,
        'Y': 0.002,
        'Z': 0.001,
        'S': 0.003,
        'T': 0.005,
        'Rx': 0.002,
        'Ry': 0.002,
        'Rz': 0.002,
        'CNOT': 0.01,
        'CZ': 0.012
    }
    plot_gate_fidelities(gate_data, 'benchmark_plots/gate_fidelities.png')
    
    shot_files = ['xeb_shots.txt']
    if os.path.exists('xeb_shots.txt'):
        plot_correlations(shot_files, 'benchmark_plots/correlations.png')


if __name__ == '__main__':
    main()