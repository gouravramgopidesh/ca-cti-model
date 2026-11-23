import subprocess, sys
for script in ['activity-10.1/bank-transfer.py','activity-10.1-try-it-yourself/retry-transfer.py','activity-10.2/inventory-reservation.py']:
    subprocess.run([sys.executable,script],check=True)
print('Completed. Evidence is in evidence folder.')
