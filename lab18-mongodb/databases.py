from collections import defaultdict, Counter
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo import UpdateOne
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args
from cassandra import ConsistencyLevel
from neo4j import GraphDatabase
from common import *

FIELD_LIST=', '.join(FIELDS)
TYPES={k:'text' for k in FIELDS}; TYPES.update(timestamp='bigint',source_count='int')
DDL=', '.join(f'{k} {TYPES[k]}' for k in FIELDS)

class Mongo:
    name='MongoDB'
    def __init__(self):
        self.client=MongoClient('mongodb://mongo:27017',serverSelectionTimeoutMS=10000,maxPoolSize=10)
        self.db=self.client.lab18_capstone
    def reset(self):
        self.client.drop_database('lab18_capstone')
        c=self.db.full_threats
        c.create_index('id',unique=True)
        c.create_index([('from_source',ASCENDING),('timestamp',DESCENDING),('id',ASCENDING)])
        c.create_index([('threat_type',ASCENDING),('day',ASCENDING)])
        c.create_index('day')
    def insert(self, rows):
        self.db.full_threats.insert_many([dict(r) for r in rows],ordered=False)
        groups=defaultdict(list)
        for r in rows: groups[r['from_source']].append(r)
        ops=[]
        for source, group in groups.items():
            ops.append(UpdateOne({'_id':source},{'$setOnInsert':{'from_source':source},'$push':{'recent_threats':{'$each':order_history(group)[:50],'$sort':{'timestamp':-1,'id':1},'$slice':50}}},upsert=True))
        self.db.threats.bulk_write(ops,ordered=False)
    def history(self, source, days):
        return [canonical(r) for r in self.db.full_threats.find({'from_source':source},{'_id':0}).sort([('timestamp',-1),('id',1)]).limit(50)]
    def recent(self, source):
        return self.db.threats.find_one({'_id':source})['recent_threats']
    def spread(self, kind, day):
        return summarize_spread(self.db.full_threats.find({'threat_type':kind,'day':day},{'_id':0,'target':1,'network':1,'indicator':1,'publisher':1}))
    def daily(self, partitions):
        return {r['_id']:r['n'] for r in self.db.full_threats.aggregate([{'$group':{'_id':'$day','n':{'$sum':1}}}])}
    def all_rows(self):
        return [canonical(r) for r in self.db.full_threats.find({},{'_id':0})]
    def by_ids(self, ids):
        return {r['id']:canonical(r) for r in self.db.full_threats.find({'id':{'$in':ids}},{'_id':0})}
    def close(self): self.client.close()

class Cassandra:
    name='Cassandra'
    def __init__(self):
        self.cluster=Cluster(['cassandra'],connect_timeout=15,executor_threads=8)
        self.s=self.cluster.connect(); self.s.default_timeout=120
        self.s.default_consistency_level=ConsistencyLevel.ONE
    def reset(self):
        self.s.execute('DROP KEYSPACE IF EXISTS lab18_capstone')
        self.s.execute("CREATE KEYSPACE lab18_capstone WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
        self.s.set_keyspace('lab18_capstone')
        for table,key in [('threats_by_source','from_source'),('threats_by_type','threat_type')]:
            self.s.execute(f'CREATE TABLE {table} ({DDL}, PRIMARY KEY (({key}, day), timestamp, id)) WITH CLUSTERING ORDER BY (timestamp DESC, id ASC)')
        qs=','.join('?' for _ in FIELDS)
        self.inserts=[self.s.prepare(f'INSERT INTO {table} ({FIELD_LIST}) VALUES ({qs})') for table in ('threats_by_source','threats_by_type')]
        self.hist=self.s.prepare(f'SELECT {FIELD_LIST} FROM threats_by_source WHERE from_source=? AND day=? LIMIT 50')
        self.sp=self.s.prepare('SELECT target, network, indicator, publisher FROM threats_by_type WHERE threat_type=? AND day=?')
        self.count=self.s.prepare('SELECT count(*) AS n FROM threats_by_type WHERE threat_type=? AND day=?')
        self.all_type=self.s.prepare(f'SELECT {FIELD_LIST} FROM threats_by_type WHERE threat_type=? AND day=?')
        self.all_source=self.s.prepare(f'SELECT {FIELD_LIST} FROM threats_by_source WHERE from_source=? AND day=?')
    def insert(self, rows):
        args=[tuple(r[k] for k in FIELDS) for r in rows]
        for stmt in self.inserts:
            # Concurrent prepared writes across partitions; no huge logged cross-partition batch.
            execute_concurrent_with_args(self.s,stmt,args,concurrency=64,raise_on_first_error=True)
    def history(self, source, days):
        rows=[]
        for day in days: rows.extend(canonical(r._asdict()) for r in self.s.execute(self.hist,(source,day)))
        return order_history(rows)[:50]
    def spread(self, kind, day):
        return summarize_spread(r._asdict() for r in self.s.execute(self.sp,(kind,day)))
    def daily(self, partitions):
        counts=Counter()
        for kind,day in partitions: counts[day]+=self.s.execute(self.count,(kind,day)).one().n
        return dict(counts)
    def all_rows(self, partitions, by_source=False):
        stmt=self.all_source if by_source else self.all_type
        return [canonical(r._asdict()) for p in partitions for r in self.s.execute(stmt,p)]
    def close(self): self.cluster.shutdown()

class Neo:
    name='Neo4j'
    def __init__(self):
        self.driver=GraphDatabase.driver('bolt://neo4j:7687',auth=('neo4j','lab18demo123'),max_connection_pool_size=10)
        self.driver.verify_connectivity()
    def query(self,q,**params):
        with self.driver.session(database='neo4j') as s:
            return [r.data() for r in s.run(q,**params)]
    def write(self,q,**params):
        with self.driver.session(database='neo4j') as s:
            return s.execute_write(lambda tx: tx.run(q,**params).consume())
    def reset(self):
        # Dedicated Compose Neo4j volume only. Delete in batches to bound transaction memory.
        while True:
            with self.driver.session(database='neo4j') as s:
                n=s.execute_write(lambda tx: tx.run('MATCH (n) WITH n LIMIT 5000 DETACH DELETE n RETURN count(*) AS n').single()['n'])
            if n==0: break
        for label,field in [('Threat','id'),('Source','name'),('Indicator','value'),('Network','prefix'),('Community','id')]:
            self.write(f'CREATE CONSTRAINT {label.lower()}_key IF NOT EXISTS FOR (n:{label}) REQUIRE n.{field} IS UNIQUE')
        self.write('CREATE INDEX threat_history IF NOT EXISTS FOR (t:Threat) ON (t.from_source,t.timestamp)')
        self.write('CREATE INDEX threat_type_day IF NOT EXISTS FOR (t:Threat) ON (t.threat_type,t.day)')
        self.write('CREATE INDEX threat_day IF NOT EXISTS FOR (t:Threat) ON (t.day)')
        self.query('CALL db.awaitIndexes(120)')
    def insert(self, rows):
        self.write('''UNWIND $rows AS r
          MERGE (s:Source {name:r.from_source}) SET s.publisher=r.publisher
          CREATE (t:Threat) SET t=r
          MERGE (i:Indicator {value:r.indicator})
          MERGE (n:Network {prefix:r.network})
          MERGE (s)-[:REPORTED]->(t)
          MERGE (t)-[:OBSERVES]->(i)
          MERGE (i)-[:IN_NETWORK]->(n)''',rows=rows)
    def history(self, source, days):
        return [canonical(r['row']) for r in self.query('''MATCH (:Source {name:$source})-[:REPORTED]->(t:Threat)
          RETURN properties(t) AS row ORDER BY t.timestamp DESC,t.id ASC LIMIT 50''',source=source)]
    def spread(self, kind, day):
        return summarize_spread(self.query('''MATCH (t:Threat {threat_type:$kind,day:$day})-[:OBSERVES]->(i:Indicator)-[:IN_NETWORK]->(n:Network)
          RETURN t.target AS target,n.prefix AS network,i.value AS indicator,t.publisher AS publisher''',kind=kind,day=day))
    def daily(self, partitions):
        return {r['day']:r['n'] for r in self.query('MATCH (t:Threat) RETURN t.day AS day,count(*) AS n')}
    def all_rows(self):
        return [canonical(r['row']) for r in self.query('MATCH (t:Threat) RETURN properties(t) AS row')]
    def close(self): self.driver.close()

def summarize_spread(rows):
    groups=defaultdict(lambda: {'observations':0,'ips':set(),'networks':set(),'publishers':set()})
    for r in rows:
        g=groups[r['target']]; g['observations']+=1; g['ips'].add(r['indicator']); g['networks'].add(r['network']); g['publishers'].add(r['publisher'])
    return {k:{'observations':v['observations'],'unique_indicators':len(v['ips']),'network_prefixes':len(v['networks']),'publishers':len(v['publishers'])} for k,v in sorted(groups.items())}
