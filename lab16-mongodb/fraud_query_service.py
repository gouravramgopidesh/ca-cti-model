import time

class CircuitBreaker:
    def __init__(self, clock=time.monotonic, threshold=3, cooldown=30):
        self.clock, self.threshold, self.cooldown = clock, threshold, cooldown
        self.failures = 0
        self.opened = None
    def call(self, fn):
        if self.opened is not None and self.clock()-self.opened < self.cooldown:
            return {'available': False, 'error': 'circuit open', 'data': None}
        try:
            value = fn()
        except Exception as exc:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened = self.clock()
            return {'available': False, 'error': type(exc).__name__, 'data': None}
        self.failures, self.opened = 0, None
        return {'available': True, 'data': value}

class FraudQueryService:
    def __init__(self, mongo=None, cassandra=None, neo=None, clock=time.monotonic):
        self.cluster = None
        self.owned = mongo is None and cassandra is None and neo is None
        if self.owned:
            from pymongo import MongoClient
            from cassandra.cluster import Cluster
            from neo4j import GraphDatabase
            mongo = MongoClient('mongodb://mongo:27017/?maxPoolSize=10', serverSelectionTimeoutMS=4000, socketTimeoutMS=5000)
            self.cluster = Cluster(['cassandra'], executor_threads=4, connect_timeout=10, control_connection_timeout=10)
            cassandra = self.cluster.connect()
            cassandra.default_timeout = 5
            neo = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j','lab16demo123'), max_connection_pool_size=10, connection_timeout=5, connection_acquisition_timeout=5)
        self.mongo, self.cassandra, self.neo = mongo, cassandra, neo
        self.breakers = {k:CircuitBreaker(clock) for k in ('mongo','cassandra','neo4j')}
    def get_transaction(self, txn_id):
        return self.breakers['mongo'].call(lambda: self.mongo.lab16_fraud.transactions.find_one({'txn_id':txn_id},{'_id':0}))
    def get_user_profile(self, user_id):
        return self.breakers['cassandra'].call(lambda: [r._asdict() for r in self.cassandra.execute('SELECT * FROM lab16_fraud.user_profiles WHERE user_id=%s ORDER BY event_time DESC LIMIT 10',(user_id,))])
    def detect_fraud_rings(self, user_id, max_hops=3):
        if type(max_hops) is not int or not 1 <= max_hops <= 3:
            raise ValueError('max_hops must be 1, 2 or 3')
        def query():
            with self.neo.session(database='neo4j') as session:
                return [r.data() for r in session.run(f'MATCH p=(u:FraudUser {{id:$uid}})-[:TRANSFERRED_TO*1..{max_hops}]->(v:FraudUser) RETURN [n IN nodes(p) | n.id] AS accounts, length(p) AS hops, v.id=u.id AS closes_ring ORDER BY hops, accounts LIMIT 50',uid=user_id)]
        return self.breakers['neo4j'].call(query)
    def analyze(self, txn_id, user_id, max_hops=3):
        return {'transaction':self.get_transaction(txn_id),'profile':self.get_user_profile(user_id),'graph':self.detect_fraud_rings(user_id,max_hops)}
    def close(self):
        if self.owned:
            self.mongo.close(); self.cluster.shutdown(); self.neo.close()
