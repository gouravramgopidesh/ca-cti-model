"""Graph-derived candidate communities, not ground-truth false positives."""
from collections import Counter, defaultdict
from itertools import combinations
from statistics import median
import networkx as nx
from common import *

def detect(neo,mongo):
    # Distinct feed pair overlaps using graph paths; exclude same publisher's subfeeds.
    overlaps=neo.query('''MATCH (s:Source)-[:REPORTED]->(:Threat)-[:OBSERVES]->(i:Indicator)
      WITH i,collect(DISTINCT s) AS sources
      UNWIND sources AS a UNWIND sources AS b
      WITH a,b,i WHERE a.name < b.name AND a.publisher <> b.publisher
      WITH a,b,count(DISTINCT i) AS shared WHERE shared >= 3
      MERGE (a)-[r:SUSPICIOUS]->(b) SET r.shared_indicators=shared,
        r.basis='shared reports; not independent evidence or maliciousness'
      RETURN a.name AS source_a,b.name AS source_b,shared ORDER BY shared DESC''')
    # Rank multi-publisher networks across the full graph. Candidate projection is bounded.
    ranked=neo.query('''MATCH (t:Threat)-[:OBSERVES]->(i:Indicator)-[:IN_NETWORK]->(n:Network)
      WITH n,count(DISTINCT t) AS observations,count(DISTINCT i) AS indicators,
      count(DISTINCT t.publisher) AS publishers
      WHERE indicators >= 3 AND publishers >= 2
      RETURN n.prefix AS prefix,observations,indicators,publishers
      ORDER BY observations DESC,prefix ASC''')
    baseline=median([r['observations']/r['indicators'] for r in ranked]) if ranked else 0
    graph=nx.Graph(); details={}; selected=ranked[:30]
    for network in selected:
        rows=neo.query('''MATCH (:Network {prefix:$prefix})<-[:IN_NETWORK]-(i:Indicator)<-[:OBSERVES]-(t:Threat)
          RETURN properties(t) AS row ORDER BY t.id LIMIT 100''',prefix=network['prefix'])
        records=[canonical(x['row']) for x in rows]
        for r in records: graph.add_node(r['id']); details[r['id']]=r
        for a,b in combinations(records,2):
            # Same exact indicator strongly connects observations; same prefix across publishers weakly connects.
            if a['indicator']==b['indicator']: weight=3
            elif a['publisher']!=b['publisher']: weight=1
            else: continue
            graph.add_edge(a['id'],b['id'],weight=weight)
    # Cross-reference the entire sampled projection, even if no candidate passes the threshold.
    projected_matches=0
    for batch in chunks(sorted(details),500):
        matched=mongo.by_ids(batch)
        if len(matched)!=len(batch) or any(matched[x]!=details[x] for x in batch):
            raise AssertionError('Projected graph / MongoDB data mismatch')
        projected_matches+=len(matched)
    if graph.number_of_edges():
        parts=nx.community.louvain_communities(graph,weight='weight',seed=18)
    else: parts=[]
    results=[]
    for ids in sorted(parts,key=lambda x:(-len(x),min(x))):
        if len(ids)<3: continue
        sub=graph.subgraph(ids); records=[details[x] for x in sorted(ids)]
        pubs={r['publisher'] for r in records}; unique={r['indicator'] for r in records}
        if len(pubs)<2: continue
        ratio=len(records)/len(unique); density=nx.density(sub)
        if density<0.35 or ratio<=baseline: continue
        # Verify exact graph document against source-of-truth MongoDB.
        matched=mongo.by_ids(sorted(ids))
        if len(matched)!=len(ids) or any(matched[r['id']]!=r for r in records):
            raise AssertionError('Graph / MongoDB community data mismatch')
        cid=f'community-{len(results)+1:03}'
        neo.write('''MERGE (c:Community {id:$id}) SET c.density=$density,c.review_status='needs_review'
           WITH c UNWIND $ids AS id MATCH (t:Threat {id:id}) MERGE (t)-[:IN_COMMUNITY]->(c)''',id=cid,density=density,ids=sorted(ids))
        results.append(dict(community_id=cid,observations=len(ids),unique_indicators=len(unique),publishers=sorted(pubs),density=density,observation_per_indicator=ratio,baseline_observation_per_indicator=baseline,review_status='needs_review',mongo_exact_matches=len(matched),members=sorted(ids),sample_details=records[:3]))
    # A zero-result detector is valid, but not misrepresented as a positive discovery.
    return dict(method='Neo4j Cypher projection; seeded NetworkX weighted Louvain; community memberships written to Neo4j',source_suspicious_edges=overlaps,eligible_networks=len(ranked),network_baseline_median=baseline,selected_networks=len(selected),projection_nodes=graph.number_of_nodes(),projection_edges=graph.number_of_edges(),projected_mongo_matches=projected_matches,all_louvain_communities=len(parts),flagged_communities=results,threshold='>=3 observations, >=2 publishers, density >=0.35, observations/unique indicators above full eligible-network median',limitations='Bounded top 30 networks, 100 observations each. IP prefixes do not establish common ownership; overlapping aggregators are not independent. Candidates are for analyst review, not confirmed false positives. No precision or recall claimed without labels.')
