import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import local, atlas, record

def main():
    with local() as a, atlas() as b:
        a.admin.command('ping'); b.admin.command('ping')
        x, y = a.server_info(), b.server_info()
        fields = ('version','gitVersion','bits','versionArray')
        data = {'local_community': {k:x.get(k) for k in fields},
                'atlas': {k:y.get(k) for k in fields},
                'comparison_scope': 'Local Community Server vs Atlas; no Docker (assignment deviation)',
                'same_version': x['version'] == y['version']}
        for key, value in data.items(): print(key, ':', value)
        record('server_comparison', 'activity-2.1-try', data)
    print('LAB 2.1 TRY PASSED: both live servers compared')

if __name__ == '__main__': main()
