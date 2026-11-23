import urllib.request, time
from pathlib import Path
from common import save
url='http://exporter:9216/metrics'
for i in range(30):
    try:
        with urllib.request.urlopen(url,timeout=10) as r: metrics=r.read().decode()
        if any(line.startswith('mongodb_up') and line.split()[-1]=='1' for line in metrics.splitlines()): break
    except (OSError, ValueError): pass
    time.sleep(2)
else: raise RuntimeError('Exporter did not report mongodb_up 1')
lines=[line for line in metrics.splitlines() if line.startswith('mongodb_')]
assert len(lines)>1
Path('/work/evidence/13.1-prometheus-metrics.txt').write_text(metrics,encoding='utf-8')
save('13.1-exporter.json',{'passed':True,'endpoint':url,'mongo_metric_count':len(lines),'examples':lines[:12]})
