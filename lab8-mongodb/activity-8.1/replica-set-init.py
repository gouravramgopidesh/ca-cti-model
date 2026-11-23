import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab8_common import *

# START-WINDOWS uses the accompanying mongosh script to initialize rs0.
with connect() as c:
    ready(c)
    # Restore the baseline on repeated runs, without deleting data.
    cfg = c.admin.command("replSetGetConfig")["config"]
    if any(m.get("arbiterOnly") for m in cfg["members"]):
        cfg["members"] = [m for m in cfg["members"] if not m.get("arbiterOnly")]
        cfg["version"] += 1
        c.admin.command({"replSetReconfig": cfg})
        wait(lambda: len(status(c)) == 3)
    # Keep current primary preferred until the priority experiment.
    cfg = c.admin.command("replSetGetConfig")["config"]
    current = primary(c)
    for m in cfg["members"]:
        m["priority"] = 2 if m["host"] == current else 1
    cfg["version"] += 1
    c.admin.command({"replSetReconfig": cfg})
    ready(c)
    print("Initial replica set status:"); show(c)
    key=collection(c).insert_one({"title":"Replication verification", "kind":"lab8-test", "createdAt":datetime.now(timezone.utc)}).inserted_id
    print("Majority+journal insert:",key,"primary:",primary(c))
    assert collection(c).find_one({"_id":key})
    observed=[]
    for host in NODES:
        with direct(host) as d:
            doc=wait(lambda: collection(d).find_one({"_id":key}))
            role=d.admin.command("hello")
            row={"host":host,"role":"PRIMARY" if role.get("isWritablePrimary") else "SECONDARY", "document":str(doc["_id"])}
            observed.append(row); print(row)
    assert sum(x["role"]=="SECONDARY" for x in observed)==2
    save("8.1-replication",{"members":show(c),"verified":observed})
