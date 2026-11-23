import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'activity-9.1'))
from benchmark import benchmark
rows=benchmark([True,False],'9.1-journaling')
print('\nJournaling comparison (measured, not predicted):')
for label in ['w:1','w:majority','w:all']:
    on=next(r['average_ms'] for r in rows if r['concern']==label and r['j'] is True)
    off=next(r['average_ms'] for r in rows if r['concern']==label and r['j'] is False)
    print(f'{label}: j:true {on:.3f} ms, j:false {off:.3f} ms, difference {on-off:+.3f} ms')
