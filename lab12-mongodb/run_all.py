import subprocess, sys
for script in ['activity-12.1/rbac.py','activity-12.1-try-it-yourself/redaction.py','activity-12.2/tls-test.py']:
    subprocess.run([sys.executable,script],check=True)
print('All Lab 12 tests passed.')
