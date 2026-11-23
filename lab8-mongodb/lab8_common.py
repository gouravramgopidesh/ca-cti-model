import os, time, json
from datetime import datetime, timezone
from pathlib import Path
from pymongo import MongoClient, monitoring, ReadPreference
from pymongo.errors import PyMongoError
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
URI = os.getenv("MONGO_URI", "mongodb://mongo1,mongo2,mongo3/?replicaSet=rs0")
DB = os.getenv("DB_NAME", "lab8-mongodb")
NODES = [f"mongo{i}:27017" for i in range(1,4)]
class ReadLog(monitoring.CommandListener):
    last_read = None
    def started(self,event):
        if event.command_name == "find": print("READ SENT TO", event.connection_id, flush=True)
    def succeeded(self,event):
        if event.command_name == "find":
            self.last_read = event.connection_id
            print("READ OK FROM", event.connection_id, flush=True)
    def failed(self,event):
        if event.command_name == "find": print("READ FAILED AT", event.connection_id, flush=True)
def connect(listener=False):
    return MongoClient(URI, serverSelectionTimeoutMS=4000, connectTimeoutMS=3000,
                       event_listeners=[listener if isinstance(listener, ReadLog) else ReadLog()] if listener else [])
def direct(host):
    return MongoClient("mongodb://"+host, directConnection=True, serverSelectionTimeoutMS=3000, read_preference=ReadPreference.SECONDARY_PREFERRED)
def wait(fn, timeout=120):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:
            result=fn()
            if result: return result
        except PyMongoError: pass
        time.sleep(1)
    raise RuntimeError("Timed out waiting for replica set condition")
def primary(c):
    return c.admin.command("hello").get("primary")
def status(c):
    s=c.admin.command("replSetGetStatus")
    return [{"name":m["name"],"state":m["stateStr"],"health":m["health"]} for m in s["members"]]
def show(c):
    rows=status(c); print(json.dumps(rows,indent=2)); return rows
def ready(c, arb=False):
    return wait(lambda: healthy(c,arb))
def healthy(c,arb):
    rows=status(c)
    return rows if sum(m["state"] in ("PRIMARY","SECONDARY") and m["health"]==1 for m in rows)==3 and (not arb or any(m["state"]=="ARBITER" and m["health"]==1 for m in rows)) else None
def collection(c):
    return c[DB].get_collection("lab8Replication",write_concern=WriteConcern(w="majority",j=True,wtimeout=15000),read_concern=ReadConcern("majority"))
def step(c,seconds=20):
    old=primary(c); print("Step down:",old,flush=True)
    try:
        with direct(old) as d: print(d.admin.command({"replSetStepDown":seconds,"secondaryCatchUpPeriodSecs":10}))
    except PyMongoError as e: print("Step-down response:",type(e).__name__,str(e),flush=True)
    return old
def new_primary(c,old):
    return wait(lambda: changed(c,old))
def changed(c,old):
    h=primary(c); return h if h and h!=old else None
def save(name,data):
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence",name+".json").write_text(json.dumps({"utc":datetime.now(timezone.utc).isoformat(),**data},indent=2,default=str))
