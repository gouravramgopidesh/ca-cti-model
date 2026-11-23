import csv, json, statistics, time, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fraud_query_service import FraudQueryService

E=Path('evidence'); E.mkdir(exist_ok=True)
def save(name,obj):
    (E/name).write_text(json.dumps(obj,indent=2,default=str),encoding='utf8')
def measure(rows, activity, backend, operation, fn, runs=20):
    fn(); times=[]
    for _ in range(runs):
        start=time.perf_counter(); fn(); times.append((time.perf_counter()-start)*1000)
    row=dict(activity=activity,backend=backend,operation=operation,runs=runs,mean_ms=statistics.mean(times),median_ms=statistics.median(times),min_ms=min(times),max_ms=max(times))
    rows.append(row); print(row)
def cy(s,q,**kw):
    with s.neo.session(database='neo4j') as session:
        return [r.data() for r in session.run(q,**kw)]
def university(s,rows):
    m=s.mongo.lab16_university; c=s.cassandra
    students={f'S{i:03}': sorted({f'C{(i+j*3)%12:02}' for j in range(3)}) for i in range(60)}
    courses={f'C{i:02}':sorted(k for k,v in students.items() if f'C{i:02}' in v) for i in range(12)}
    m.students.delete_many({}); m.courses.delete_many({})
    m.students.insert_many([{'_id':k,'course_ids':v} for k,v in students.items()]); m.courses.insert_many([{'_id':k,'student_ids':v} for k,v in courses.items()]); m.students.create_index('course_ids')
    c.execute("CREATE KEYSPACE IF NOT EXISTS lab16_university WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
    c.execute('CREATE TABLE IF NOT EXISTS lab16_university.student_courses (student_id text, course_id text, PRIMARY KEY (student_id,course_id))')
    c.execute('CREATE TABLE IF NOT EXISTS lab16_university.course_students (course_id text, student_id text, PRIMARY KEY (course_id,student_id))')
    for table in ('student_courses','course_students'): c.execute('TRUNCATE lab16_university.'+table)
    for st,cs in students.items():
        for co in cs:
            c.execute('INSERT INTO lab16_university.student_courses (student_id,course_id) VALUES (%s,%s)',(st,co)); c.execute('INSERT INTO lab16_university.course_students (course_id,student_id) VALUES (%s,%s)',(co,st))
    cy(s,'MATCH (n:LabStudent) DETACH DELETE n'); cy(s,'MATCH (n:LabCourse) DETACH DELETE n')
    cy(s,'CREATE CONSTRAINT lab_student_id IF NOT EXISTS FOR (n:LabStudent) REQUIRE n.id IS UNIQUE'); cy(s,'CREATE CONSTRAINT lab_course_id IF NOT EXISTS FOR (n:LabCourse) REQUIRE n.id IS UNIQUE')
    cy(s,'UNWIND $ids AS id CREATE (:LabStudent {id:id})',ids=list(students)); cy(s,'UNWIND $ids AS id CREATE (:LabCourse {id:id})',ids=list(courses))
    cy(s,'UNWIND $pairs AS x MATCH (a:LabStudent {id:x.s}),(b:LabCourse {id:x.c}) CREATE (a)-[:ENROLLED_IN]->(b)',pairs=[dict(s=k,c=v) for k,vs in students.items() for v in vs])
    def mc(k): return sorted(m.students.find_one({'_id':k})['course_ids'])
    def ms(k): return sorted(m.courses.find_one({'_id':k})['student_ids'])
    def mp(k): return sorted(x['_id'] for x in m.students.find({'_id':{'$ne':k},'course_ids':{'$in':mc(k)}},{'_id':1}))
    def cc(k): return sorted(r.course_id for r in c.execute('SELECT course_id FROM lab16_university.student_courses WHERE student_id=%s',(k,)))
    def cs(k): return sorted(r.student_id for r in c.execute('SELECT student_id FROM lab16_university.course_students WHERE course_id=%s',(k,)))
    def cp(k): return sorted({v for co in cc(k) for v in cs(co)}-{k})
    def nc(k): return [r['id'] for r in cy(s,'MATCH (:LabStudent {id:$k})-[:ENROLLED_IN]->(c:LabCourse) RETURN c.id AS id ORDER BY id',k=k)]
    def ns(k): return [r['id'] for r in cy(s,'MATCH (a:LabStudent)-[:ENROLLED_IN]->(:LabCourse {id:$k}) RETURN a.id AS id ORDER BY id',k=k)]
    def np(k): return [r['id'] for r in cy(s,'MATCH (a:LabStudent {id:$k})-[:ENROLLED_IN]->(:LabCourse)<-[:ENROLLED_IN]-(b:LabStudent) WHERE a<>b RETURN DISTINCT b.id AS id ORDER BY id',k=k)]
    evidence=[]
    for op,keys,expected,funcs in [('courses_for_student',students,lambda k:students[k],(mc,cc,nc)),('students_in_course',courses,lambda k:courses[k],(ms,cs,ns)),('students_sharing_course',students,lambda k:sorted({v for co in students[k] for v in courses[co]}-{k}),(mp,cp,np))]:
        for k in keys:
            actual=[f(k) for f in funcs]; assert all(x==expected(k) for x in actual),(op,k,actual)
            evidence.append(dict(operation=op,key=k,expected=expected(k),mongodb=actual[0],cassandra=actual[1],neo4j=actual[2]))
        k=next(iter(keys))
        for backend,f in zip(('MongoDB','Cassandra','Neo4j'),funcs): measure(rows,'16.1',backend,op,lambda f=f:f(k))
    save('university_results.json',evidence); print('LAB 16.1 PASSED: 60 students, 12 courses, 180 enrollments; all queries agree')
def fraud(s,rows):
    m=s.mongo.lab16_fraud; c=s.cassandra
    m.transactions.delete_many({}); m.transactions.create_index('txn_id',unique=True)
    t=datetime(2025,1,1,tzinfo=timezone.utc)
    tx=[dict(txn_id=f'T{i:03}',user_id='U1',amount=100+i,merchant='Demo merchant',timestamp=t+timedelta(minutes=i),risk_score=0.9 if i==0 else 0.2) for i in range(15)]
    m.transactions.insert_many([dict(x) for x in tx])
    c.execute("CREATE KEYSPACE IF NOT EXISTS lab16_fraud WITH replication = {'class':'SimpleStrategy','replication_factor':1}")
    c.execute('CREATE TABLE IF NOT EXISTS lab16_fraud.user_profiles (user_id text,event_time timestamp,txn_id text,amount double,merchant text, PRIMARY KEY (user_id,event_time,txn_id)) WITH CLUSTERING ORDER BY (event_time DESC,txn_id ASC)')
    c.execute('TRUNCATE lab16_fraud.user_profiles')
    for x in tx: c.execute('INSERT INTO lab16_fraud.user_profiles (user_id,event_time,txn_id,amount,merchant) VALUES (%s,%s,%s,%s,%s)',(x['user_id'],x['timestamp'],x['txn_id'],float(x['amount']),x['merchant']))
    cy(s,'MATCH (n:FraudUser) DETACH DELETE n'); cy(s,'CREATE CONSTRAINT lab_fraud_user IF NOT EXISTS FOR (n:FraudUser) REQUIRE n.id IS UNIQUE')
    cy(s,'UNWIND $ids AS id CREATE (:FraudUser {id:id})',ids=['U1','U2','U3','U4','U5'])
    cy(s,'UNWIND $edges AS e MATCH (a:FraudUser {id:e[0]}),(b:FraudUser {id:e[1]}) CREATE (a)-[:TRANSFERRED_TO]->(b)',edges=[['U1','U2'],['U2','U3'],['U3','U1'],['U2','U4'],['U4','U5']])
    result=s.analyze('T000','U1'); assert all(v['available'] for v in result.values()),result
    assert result['transaction']['data']['txn_id']=='T000'; assert [x['txn_id'] for x in result['profile']['data']]==[f'T{i:03}' for i in range(14,4,-1)]
    assert any(x['closes_ring'] and x['accounts']==['U1','U2','U3','U1'] for x in result['graph']['data'])
    save('fraud_analysis.json',result)
    def checked(fn):
        r=fn(); assert r['available'],r; return r
    measure(rows,'16.2','MongoDB','get_transaction',lambda:checked(lambda:s.get_transaction('T000')))
    measure(rows,'16.2','Cassandra','get_user_profile',lambda:checked(lambda:s.get_user_profile('U1')))
    for hops in (1,2,3):
        r=checked(lambda:s.detect_fraud_rings('U1',hops)); assert r['data'] and all(x['hops']<=hops for x in r['data'])
        measure(rows,'16.2','Neo4j',f'graph_{hops}_hop',lambda:checked(lambda:s.detect_fraud_rings('U1',hops)))
    print('LAB 16.2 PASSED: merged fraud analysis, ordered history and three-hop ring')
def main():
    suite=unittest.defaultTestLoader.discover('.',pattern='test_unit.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); assert result.wasSuccessful()
    save('unit_tests.json',dict(tests=result.testsRun,passed=True))
    s=FraudQueryService(); rows=[]
    try: university(s,rows); fraud(s,rows)
    finally: s.close()
    save('benchmarks.json',rows)
    with (E/'benchmarks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print('LAB 16 PASSED: 16.1 and 16.2')
if __name__=='__main__': main()
