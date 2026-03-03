"""
gate_characterization_qpu.py — H Gate Behavior Test on QPU-1
============================================================
Pure Qreg code. Demonstrates that H·H = X on QPU-1,
not H·H = I as in the standard Hadamard definition.

Run on QPU-1 on 2026-03-03.
"""

q = Qreg(10)

# Test 1: reset -> measure (expect: 0000000000)
q.reset_all()
bits = q.measure()
print('TEST1_RESET: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 2: reset -> H_all -> measure (superposition, random)
q.reset_all()
q.H_all()
bits = q.measure()
print('TEST2_H: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 3: reset -> H_all -> H_all -> measure (expect: 0000000000, got: 1111111111)
q.reset_all()
q.H_all()
q.H_all()
bits = q.measure()
print('TEST3_HH: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 4: reset -> X_all -> measure (expect: 1111111111)
q.reset_all()
q.X_all()
bits = q.measure()
print('TEST4_X: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 5: reset -> H(0) -> H(0) -> measure (expect: 0, got: 1 on qubit 0)
q.reset_all()
q.H(0)
q.H(0)
bits = q.measure()
print('TEST5_HH_single: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 6: reset -> H_all -> H_range(0,10) -> measure
q.reset_all()
q.H_all()
q.H_range(0, 10)
bits = q.measure()
print('TEST6_H_all_Hrange: ' + ''.join(str(int(b)) for b in bits[:10]))

# Test 7: reset -> H_all -> X_all -> measure
q.reset_all()
q.H_all()
q.X_all()
bits = q.measure()
print('TEST7_H_X: ' + ''.join(str(int(b)) for b in bits[:10]))

print('DONE')
