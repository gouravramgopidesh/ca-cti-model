import subprocess, sys
for path in ['activity-11.1/shard-key-evaluation.py','activity-11.2/hotspot-detection.py']:
    subprocess.run([sys.executable,path],check=True)
print('Completed. Evidence is in evidence folder.')
