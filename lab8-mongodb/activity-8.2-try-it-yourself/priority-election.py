import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab8_common import *

with connect() as c:
    # Wait out the previous experiment's step-down exclusion period.
    time.sleep(25); ready(c)
    old=primary(c); cfg=c.admin.command("replSetGetConfig")["config"]
    candidates=[m for m in cfg["members"] if not m.get("arbiterOnly") and m["host"]!=old and m.get("votes",1)]
    assert len(candidates)==2
    for m in cfg["members"]:
        if m["host"]==old: m["priority"]=4
        elif m["host"]==candidates[0]["host"]: m["priority"]=3
        elif not m.get("arbiterOnly"): m["priority"]=1
    predicted=candidates[0]["host"]; cfg["version"]+=1
    print("Predicted primary:",predicted,flush=True)
    print(c.admin.command({"replSetReconfig":cfg})); time.sleep(8); ready(c)
    old=step(c,60); actual=new_primary(c,old)
    print("First elected primary:",actual,"Prediction matched:",actual==predicted)
    # A priority takeover can occur later; preserve both observations.
    time.sleep(12); later=primary(c); print("Primary after 12 seconds:",later)
    save("8.2-priority",{"predicted":predicted,"actual":actual,"matched":actual==predicted,"laterPrimary":later,"members":show(c),"configuration":c.admin.command("replSetGetConfig")["config"]})
