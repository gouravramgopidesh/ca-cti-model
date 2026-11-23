from pathlib import Path
import hashlib, json, datetime as dt

ROOT = Path(__file__).resolve().parent
FIELDS = ('id','from_source','publisher','timestamp','day','indicator','network','threat_type','target','source_url','source_count','timestamp_basis')
TOTAL = 100_000
INSERT_BATCH = 100
RUNS = 10
HOLDOUT = INSERT_BATCH * RUNS

def now():
    return dt.datetime.now(dt.timezone.utc)

def canonical(row):
    return {k: row[k] for k in FIELDS}

def dump_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True, default=str), encoding='utf-8')

def row_bytes(row):
    return json.dumps(canonical(row), sort_keys=True, separators=(',',':'), ensure_ascii=True).encode()

def digest(rows):
    h = hashlib.sha256()
    for row in sorted(rows, key=lambda r: r['id']):
        h.update(row_bytes(row)); h.update(b'\n')
    return h.hexdigest()

def chunks(rows, size):
    for i in range(0, len(rows), size): yield rows[i:i+size]

def order_history(rows):
    return sorted(rows, key=lambda r: (-r['timestamp'], r['id']))
