import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib.util
import pymongo
from common import local, atlas, record

def main():
    assert sys.version_info >= (3, 10), 'Python 3.10+ required'
    with local() as c:
        c.admin.command('ping')
        version = c.server_info()['version']
    with atlas() as c:
        c.admin.command('ping')
        cloud = c.server_info()['version']
    optional = {x: importlib.util.find_spec(x) is not None for x in
                ['fastapi','streamlit','voyageai','neo4j','cassandra','rich','dotenv']}
    data = dict(python=sys.version.split()[0], pymongo=pymongo.version,
                local_deployment="MongoDB Community Server", local_version=version,
                atlas_version=cloud, optional_packages=optional)
    for k,v in data.items(): print(k, ':', v)
    record('environment', 'activity-2.1', data)
    print('LAB 2.1 PASSED: local and Atlas verified')

if __name__ == '__main__': main()
