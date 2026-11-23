import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab8_common import *

import threading
with connect() as c:
    ready(c); before=show(c); old=step(c); first=new_primary(c,old)
    print("First elected primary:",first); show(c)
    # Let the former primary become eligible again before the next election.
    time.sleep(25); ready(c)
    stop=threading.Event(); rows=[]
    def monitor():
        listener = ReadLog()
        with connect(listener) as reader:
            while not stop.is_set():
                row={"utc":datetime.now(timezone.utc).isoformat()}
                try:
                    doc=collection(reader).find_one({}, {"_id":1})
                    row.update(ok=doc is not None, server=listener.last_read, primary=primary(reader))
                except PyMongoError as e: row.update(ok=False,error=str(e))
                rows.append(row); print(row,flush=True); stop.wait(1)
    t=threading.Thread(target=monitor); t.start()
    try:
        time.sleep(5); old2=step(c); second=new_primary(c,old2)
        print("Second elected primary:",second); time.sleep(8)
    finally:
        stop.set(); t.join()
    assert any(r.get("ok") and r.get("server") and f"{r['server'][0]}:{r['server'][1]}"==second for r in rows), "No successful read observed on new primary"
    save("8.2-failover",{"before":before,"firstPrimary":first,"secondOldPrimary":old2,"secondPrimary":second,"after":show(c),"reads":rows})
