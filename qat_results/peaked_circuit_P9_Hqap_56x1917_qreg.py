# QPU-1 Qreg for peaked_circuit_P9_Hqap_56x1917
# n_qubits=56


import time

q = Qreg(56)
start = time.time()

for shot in range(1000):
    q.reset_all()
    

    bits = q.measure()
    bs = "".join(str(int(b)) for b in bits[:56])
    print("SHOT:" + bs)

elapsed = time.time() - start
print("ELAPSED:" + str(elapsed))
print("DONE")
