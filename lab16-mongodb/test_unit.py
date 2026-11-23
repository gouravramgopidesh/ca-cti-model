import unittest
from unittest.mock import MagicMock
from fraud_query_service import FraudQueryService

class Tests(unittest.TestCase):
    def setUp(self):
        self.now=0; self.m=MagicMock(); self.c=MagicMock(); self.n=MagicMock()
        self.find=self.m.lab16_fraud.transactions.find_one
        self.find.return_value={'txn_id':'T1'}
        row=MagicMock(); row._asdict.return_value={'txn_id':'T1'}; self.c.execute.return_value=[row]
        record=MagicMock(); record.data.return_value={'accounts':['U1','U2'],'hops':1}; self.n.session.return_value.__enter__.return_value.run.return_value=[record]
        self.s=FraudQueryService(self.m,self.c,self.n,clock=lambda:self.now)
    def test_merge(self):
        r=self.s.analyze('T1','U1'); self.assertTrue(all(v['available'] for v in r.values())); self.assertEqual(r['transaction']['data']['txn_id'],'T1'); self.assertEqual(r['profile']['data'],[{'txn_id':'T1'}]); self.assertEqual(r['graph']['data'][0]['hops'],1)
        self.find.assert_called_once_with({'txn_id':'T1'},{'_id':0}); self.c.execute.assert_called_once(); self.n.session.assert_called_once()
    def test_breakers_each_backend(self):
        for name,method,mock in [('mongo',lambda:self.s.get_transaction('T1'),self.find),('cassandra',lambda:self.s.get_user_profile('U1'),self.c.execute),('neo4j',lambda:self.s.detect_fraud_rings('U1'),self.n.session.return_value.__enter__.return_value.run)]:
            mock.side_effect=RuntimeError('offline'); before=mock.call_count
            for _ in range(3): self.assertFalse(method()['available'])
            self.assertEqual(method()['error'],'circuit open'); self.assertEqual(mock.call_count,before+3)
            self.now+=29; self.assertEqual(method()['error'],'circuit open'); self.now+=1; mock.side_effect=None
            self.assertTrue(method()['available']); self.assertEqual(self.s.breakers[name].failures,0)
    def test_partial(self):
        self.find.side_effect=RuntimeError(); r=self.s.analyze('T1','U1'); self.assertFalse(r['transaction']['available']); self.assertTrue(r['profile']['available']); self.assertTrue(r['graph']['available'])
    def test_reset(self):
        self.find.side_effect=[RuntimeError(),{'txn_id':'T1'},RuntimeError()]; self.s.get_transaction('T1'); self.s.get_transaction('T1'); self.s.get_transaction('T1'); self.assertEqual(self.s.breakers['mongo'].failures,1)
    def test_hops(self):
        for h in (0,4,'3',True):
            with self.assertRaises(ValueError): self.s.detect_fraud_rings('U1',h)
