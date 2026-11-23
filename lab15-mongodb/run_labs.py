import subprocess,sys
for script in ('activity-15.1/test_api.py','activity-15.2/migrate.py'):
    subprocess.run([sys.executable,script],check=True)
print('LAB 15 PASSED: 15.1 and 15.2')
