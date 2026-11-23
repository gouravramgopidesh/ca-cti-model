"""Small artificial fixtures for unit tests ONLY. Never used by live collector or benchmarks."""
import unittest, datetime as dt
from collect import parse_ips, make_row
from common import digest, order_history, FIELDS
from communities import detect

T=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
def row(source,ip):
    return make_row(source,source,'https://example.invalid','reported_attack','ssh',T,'fixture',ip,'8.8.8.0/24',0)

class FakeNeo:
    def __init__(self,rows): self.rows=rows; self.writes=[]
    def query(self,q,**params):
        if 'SUSPICIOUS' in q: return [{'source_a':'A','source_b':'B','shared':3}]
        if 'ORDER BY observations DESC' in q: return [{'prefix':'8.8.8.0/24','observations':6,'indicators':3,'publishers':2},{'prefix':'1.1.1.0/24','observations':3,'indicators':3,'publishers':2}]
        if 'RETURN properties(t)' in q: return [{'row':r} for r in self.rows] if params['prefix']=='8.8.8.0/24' else []
        raise AssertionError(q)
    def write(self,q,**params): self.writes.append(params)
class FakeMongo:
    def __init__(self,rows): self.rows={r['id']:r for r in rows}
    def by_ids(self,ids): return {i:self.rows[i] for i in ids if i in self.rows}

class UnitTests(unittest.TestCase):
    def test_parser(self):
        parsed=list(parse_ips('# comment\n8.8.8.8 3\n8.8.8.8\n127.0.0.1\n192.0.2.1\n2001:4860:4860::8888 1\ninvalid\n'))
        self.assertEqual(parsed,[('8.8.8.8','8.8.8.0/24',3),('2001:4860:4860::8888','2001:4860:4860::/48',1)])
    def test_record_key_and_hash(self):
        a=row('A','8.8.8.8'); b=row('B','8.8.8.8')
        self.assertEqual(set(a),set(FIELDS)); self.assertNotEqual(a['id'],b['id']); self.assertEqual(a['id'],row('A','8.8.8.8')['id'])
        self.assertEqual(digest([a,b]),digest([b,a])); self.assertNotEqual(digest([a,b]),digest([a]))
    def test_history_tie_break(self):
        a=row('A','8.8.8.8'); b=row('B','8.8.8.8'); self.assertEqual([r['id'] for r in order_history([b,a])],sorted([a['id'],b['id']]))
    def test_graph_review_and_cross_reference(self):
        rows=[row(s,ip) for s in ('A','B') for ip in ('8.8.8.8','8.8.8.9','8.8.8.10')]
        n=FakeNeo(rows); out=detect(n,FakeMongo(rows)); self.assertEqual(out['projected_mongo_matches'],6)
        self.assertGreater(out['all_louvain_communities'],0)
        # No fabricated positives: all flagged candidates must match and remain needs_review.
        for c in out['flagged_communities']:
            self.assertEqual(c['review_status'],'needs_review'); self.assertEqual(c['observations'],c['mongo_exact_matches'])
    def test_graph_missing_record_rejected(self):
        rows=[row(s,ip) for s in ('A','B') for ip in ('8.8.8.8','8.8.8.9','8.8.8.10')]
        with self.assertRaises(AssertionError): detect(FakeNeo(rows),FakeMongo(rows[:-1]))
if __name__=='__main__': unittest.main(verbosity=2)
