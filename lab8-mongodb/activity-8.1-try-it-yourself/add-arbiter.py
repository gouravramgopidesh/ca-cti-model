import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab8_common import *

with connect() as c:
    ready(c)
    cfg=c.admin.command("replSetGetConfig")["config"]
    if not any(m.get("arbiterOnly") for m in cfg["members"]):
        c.admin.command({"setDefaultRWConcern":1,"defaultWriteConcern":{"w":"majority"}})
        cfg["members"].append({"_id":3,"host":"arbiter:27017","arbiterOnly":True,"priority":0,"votes":1})
        cfg["version"]+=1
        print(c.admin.command({"replSetReconfig":cfg}))
    ready(c,True)
    print("Four votes, majority three; arbiter has no application data and cannot become primary.")
    print("A primary + secondary + arbiter configuration has three votes, but only two data copies.")
    save("8.1-arbiter",{"members":show(c),"configuration":c.admin.command("replSetGetConfig")["config"]})
