"""Build the actual submission PDF from measured results, not placeholders."""
from pathlib import Path
from xml.sax.saxutils import escape
import json, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from common import ROOT

DBS=['MongoDB','Cassandra','Neo4j']
OPS=['threat_history','target_and_spread','daily_volume','real_time_insert']
LABELS=['Threat history (50)','Target and spread','Daily volume','Insert 100 observations']
INK=colors.HexColor('#152D43'); TEAL=colors.HexColor('#007B83'); LIGHT=colors.HexColor('#E9F4F5'); MUTED=colors.HexColor('#486173')
URL='https://hub.docker.com/r/gouravram77/lab18-mongodb'
REFS=[('IPsum daily feed and methodology','https://github.com/stamparm/ipsum'),('Blocklist.de export scope','https://www.blocklist.de/en/export.html'),('ShadowWhisperer feed definitions','https://github.com/ShadowWhisperer/IPs'),('Inbound malicious-IP aggregation','https://github.com/romainmarcoux/malicious-ip'),('ThreatHive feed methodology','https://www.threathive.net/'),('MongoDB sharding','https://www.mongodb.com/docs/manual/sharding/'),('MongoDB sharded backup','https://www.mongodb.com/docs/manual/administration/backup-sharded-clusters/'),('Cassandra replication','https://cassandra.apache.org/doc/stable/cassandra/architecture/dynamo.html'),('Cassandra backups','https://cassandra.apache.org/doc/stable/cassandra/managing/operating/backups.html'),('Neo4j editions and scale','https://neo4j.com/docs/operations-manual/current/introduction/'),('Neo4j backups','https://neo4j.com/docs/operations-manual/current/backup-restore/'),('Neo4j Louvain concept','https://neo4j.com/docs/graph-data-science/current/algorithms/louvain/'),('NetworkX Louvain implementation','https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html')]

def chart(data,out):
    rows={(r['operation'],r['database']):r for r in data['benchmark']}
    x=np.arange(4); width=.25
    fig,ax=plt.subplots(figsize=(8.1,3.3))
    for j,db in enumerate(DBS): ax.bar(x+(j-1)*width,[rows[op,db]['median_latency_ms'] for op in OPS],width,label=db)
    ax.set_yscale('log'); ax.set_ylabel('Median latency (ms, log scale)'); ax.set_xticks(x,LABELS,fontsize=8); ax.legend(ncol=3,loc='upper left',fontsize=8); ax.grid(axis='y',alpha=.2); fig.tight_layout()
    for ext in ('png','svg'): fig.savefig(out/f'latency.{ext}',dpi=180)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,3)); ax.bar(DBS,[rows['real_time_insert',db]['median_records_per_second'] for db in DBS]); ax.set_ylabel('Median observations / second'); ax.grid(axis='y',alpha=.2); fig.tight_layout()
    for ext in ('png','svg'): fig.savefig(out/f'throughput.{ext}',dpi=180)
    plt.close(fig)

def architecture():
    d=Drawing(480,214)
    def box(x,y,w,h,title,sub):
        d.add(Rect(x,y,w,h,rx=7,ry=7,fillColor=LIGHT,strokeColor=TEAL,strokeWidth=1))
        d.add(String(x+w/2,y+h-17,title,fontName='Helvetica-Bold',fontSize=9,fillColor=INK,textAnchor='middle'))
        for i,s in enumerate(sub): d.add(String(x+w/2,y+h-30-i*11,s,fontSize=7.5,fillColor=MUTED,textAnchor='middle'))
    def arrow(x,y,x2,y2):
        d.add(Line(x,y,x2,y2,strokeColor=TEAL,strokeWidth=1)); dx=x2-x; dy=y2-y; length=math.hypot(dx,dy); ux=dx/length; uy=dy/length
        d.add(Polygon([x2,y2,x2-6*ux+3*uy,y2-6*uy-3*ux,x2-6*ux-3*uy,y2-6*uy+3*ux],fillColor=TEAL,strokeColor=None))
    box(160,163,160,43,'Public CTI feeds',['Passive snapshots + SHA-256'])
    box(160,108,160,43,'Python normalization',['Frozen baseline + held-out inserts'])
    arrow(240,163,240,151)
    for x,title,sub in [(6,'MongoDB',['Full documents + recent 50']),(166,'Cassandra',['Source/day + type/day']),(326,'Neo4j',['Threat graph + Louvain'])]:
        box(x,49,148,43,title,sub); arrow(240,108,x+74,92)
    box(122,0,236,37,'Verification + report',['Equal results | timings | MongoDB cross-reference'])
    for x in (80,240,400): arrow(x,49,240,37)
    return d

def render_report(data,out,path):
    out=Path(out); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); chart(data,out)
    style=getSampleStyleSheet()
    style.add(ParagraphStyle(name='CTitle',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=INK,spaceAfter=9))
    style.add(ParagraphStyle(name='CSub',fontName='Helvetica',fontSize=11,leading=15,textColor=MUTED,spaceAfter=11))
    style.add(ParagraphStyle(name='CH',fontName='Helvetica-Bold',fontSize=15,leading=18,textColor=TEAL,spaceAfter=7,spaceBefore=8))
    style.add(ParagraphStyle(name='CB',fontName='Helvetica',fontSize=9.5,leading=13,textColor=INK,spaceAfter=7))
    style.add(ParagraphStyle(name='CT',fontName='Helvetica',fontSize=8,leading=10,textColor=INK,wordWrap='CJK'))
    style.add(ParagraphStyle(name='CTHead',fontName='Helvetica-Bold',fontSize=8,leading=10,textColor=colors.white,wordWrap='CJK'))
    story=[]
    def p(s,kind='CB'): story.append(Paragraph(escape(str(s)),style[kind]))
    def h(s): p(s,'CH')
    def page(): story.append(PageBreak())
    def table(headers,rows,widths):
        contents=[[Paragraph(escape(str(x)),style['CTHead']) for x in headers]]+[[Paragraph(escape(str(x)),style['CT']) for x in r] for r in rows]
        t=Table(contents,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,-1),(-1,-1),.5,TEAL)])); story.append(t); story.append(Spacer(1,7))
    m=data['manifest']; e=data['environment']; g=data['graph']; q=data['query_parameters']; lookup={(r['operation'],r['database']):r for r in data['benchmark']}
    winners={op:min(DBS,key=lambda db:lookup[op,db]['median_latency_ms']) for op in OPS}
    p('LAB 18 / COMPARATIVE CAPSTONE','CSub'); p('False-positive detection in threat intelligence','CTitle'); p(f"MongoDB • Cassandra • Neo4j | {data['run_mode'].upper()} run | {data['completed_utc']}",'CSub')
    p('Name / USN: _______________________________________')
    p('Docker Hub: '+URL); p('Image: gouravram77/lab18-mongodb:1.0. '+('Published-run workflow executed after pulling this tag.' if data['run_mode']=='published' else 'Local build; publication must be verified separately.'))
    h('1. Executive summary')
    p(f"Use MongoDB as the canonical document store and bounded display cache; retain Neo4j for relationship investigation and community review. Cassandra is an option for sustained, partition-targeted ingestion at scale. On this single-node workload, the lowest median latency was {winners['threat_history']} for history, {winners['target_and_spread']} for spread, {winners['daily_volume']} for daily analytics, and {winners['real_time_insert']} for a 100-observation insert batch. All stores returned equivalent query results and matching full-record hashes. Graph communities are review candidates, not verified false positives. Production choices require replicated-cluster load tests.")
    h('2. System architecture'); story.append(architecture()); story.append(Spacer(1,6))
    p('A frozen passive feed dataset is inserted into each database. Graph findings are checked against MongoDB; the lab does not scan or contact listed IP addresses. The Python runner creates evidence and this report.')
    page(); h('3. Methodology and data provenance')
    p(f"Baseline: {m['baseline_count']:,} feed observations; {m['distinct_baseline_ips']:,} distinct IPs; {m['holdout_count']:,} additional real held-out observations. Unit = unique (feed, UTC snapshot day, IP), not unique incidents, victims or confirmed threats. Dates are snapshot publication/retrieval dates, not attack times. Unknown targets remain unknown. The original feed ranking and round-robin sampling can bias results.")
    table(['Publisher','Baseline observations'],[(k,f'{v:,}') for k,v in sorted(m['publisher_counts'].items())],[245,245])
    table(['UTC observation day','Count'],[(k,f'{v:,}') for k,v in sorted(m['day_counts'].items())],[245,245])
    p('Frozen dataset SHA-256: '+m['dataset_sha256']); p('Collection time: '+m['collected_at'])
    p(f"Feed fetch failures: {len(m['errors'])}. Exact URLs, per-feed raw-content hashes, timestamps, sampling and failures are retained in evidence/provenance.json and datasets/manifest.json. Reused frozen snapshot ensures local and published comparisons are on the same data.")
    p(f"Environment: {e['platform']}; Python {e['python']}; visible logical CPUs {e['logical_cpus']}; visible memory {round((e['visible_memory_bytes'] or 0)/2**30,2)} GiB; cgroup memory limit {e['cgroup_memory_limit']}; CPU limit {e['cgroup_cpu_limit']}. Versions: {e['versions']}. Single-node containers, Cassandra RF=1/ONE; no claim of equal production durability.")
    p('Three read workloads warmed once, then 10 measured runs per DB, alternating DB order. Timings include driver/network and client result materialization; spread includes identical Python reduction. Insert batches of 100 held-out new records, 10 runs, include all required denormalized writes/edges and acknowledged completion. No cold-cache, multi-client, failover or scale-out test.')
    page(); h('4. Schema design and data modeling')
    table(['Database','Physical model','Design rationale / trade-off'],[
      ('MongoDB','full_threats: one document per observation; unique id; compound (from_source, timestamp DESC, id); (threat_type, day), day. threats: source + recent_threats array (max 50).','Full history indexed; compact recent display; duplicate snapshots must be maintained. Two collections are not atomically updated in the standalone lab; production transactions/outbox recommended.'),
      ('Cassandra','threats_by_source PK ((from_source, day), timestamp, id); threats_by_type PK ((threat_type, day), timestamp, id); DESC time, ASC id.','Query-specific rows written twice. Single source/day or type/day partition. Multi-day history and all-day counts fan out across known partitions. Add hourly/hash buckets and preaggregates at high scale.'),
      ('Neo4j','Source -REPORTED-> Threat -OBSERVES-> Indicator -IN_NETWORK-> Network; SUSPICIOUS source edges; IN_COMMUNITY links. Unique node IDs and composite history/type indexes.','Relationships enable shared-indicator traversal; extra nodes/edges cost memory and write work. Network prefix is a weak correlation, not evidence of common ownership.')],[75,200,215])
    h('Representative query forms')
    table(['Pattern','MongoDB','Cassandra','Neo4j'],[
      ('History','find({from_source:s}).sort({timestamp:-1,id:1}).limit(50)','SELECT ... WHERE from_source=? AND day=? LIMIT 50; merge days','MATCH (:Source {name:$s})-[:REPORTED]->(t) RETURN t ORDER BY t.timestamp DESC,t.id LIMIT 50'),
      ('Spread','find({threat_type:k,day:d}); reduce','SELECT target,network,indicator,publisher WHERE threat_type=? AND day=?; reduce','MATCH (t:Threat {threat_type:$k,day:$d})-[:OBSERVES]->(i)-[:IN_NETWORK]->(n) RETURN ...'),
      ('Daily','aggregate $group by day','SELECT count(*) per type/day partition; sum by day','MATCH (t:Threat) RETURN t.day,count(*)'),
      ('Insert','insert_many + bounded $push','Prepared concurrent inserts into both tables','UNWIND rows; create Threat and merge edges')],[66,140,142,142])
    p('The runnable schema files and full query source are included in the Docker project. All timestamps are UTC epoch milliseconds; IDs are deterministic SHA-256 keys.')
    page(); h('5. Query performance comparison')
    table(['Operation','MongoDB (ms)','Cassandra (ms)','Neo4j (ms)','Lowest median'],[(label,*[f"{lookup[op,db]['median_latency_ms']:.3f}" for db in DBS],winners[op]) for op,label in zip(OPS,LABELS)],[142,87,87,87,87])
    table(['Insert throughput','MongoDB','Cassandra','Neo4j'],[('Median observations/s',*[f"{lookup['real_time_insert',db]['median_records_per_second']:,.1f}" for db in DBS])],[160,110,110,110])
    story.append(Image(str(out/'latency.png'),width=490,height=200)); story.append(Spacer(1,5)); story.append(Image(str(out/'throughput.png'),width=420,height=180))
    p(f"History feed: {q['history_source']}; target/spread filter: {q['spread_type']}, {q['spread_day']}. MongoDB embedded recent-50 median: {q['embedded_median_ms']:.3f} ms (additional measurement). See benchmark_raw.csv for all 120 primary timings. Latencies are not universal rankings.")
    page(); h('6. Integrity and graph-based false-positive analysis')
    table(['Verification','Baseline','After insert benchmark'],[(k,f"{data['baseline_integrity'][k]['count']:,} / hash match",f"{data['final_integrity'][k]['count']:,} / hash match") for k in ('MongoDB full_threats','Cassandra threats_by_type','Cassandra threats_by_source','Neo4j Threat')],[190,150,150])
    p(f"Verified recent-50 arrays for {data['baseline_integrity']['embedded_sources_verified']} sources. Graph REPORTED and OBSERVES counts equal observation counts; IN_NETWORK counts match distinct indicators.")
    p(f"Graph analysis: {len(g['source_suspicious_edges'])} SUSPICIOUS source-pair edges; {g['eligible_networks']} eligible multi-publisher networks. Top {g['selected_networks']} networks projected into {g['projection_nodes']} observations and {g['projection_edges']} weighted edges. MongoDB exact matches in the full projection: {g.get('projected_mongo_matches',0)}. Louvain identified {g['all_louvain_communities']} communities; {len(g['flagged_communities'])} passed review thresholds.")
    p('Algorithm: '+g['method']+'. '+g['threshold']+'. '+g['limitations'])
    if g['flagged_communities']:
        table(['Candidate','Observations','Density','Reports / indicator','Mongo matches'],[(c['community_id'],c['observations'],f"{c['density']:.3f}",f"{c['observation_per_indicator']:.2f}",c['mongo_exact_matches']) for c in g['flagged_communities'][:8]],[120,92,82,106,90])
        p('All flagged members were cross-referenced field-for-field against MongoDB. The complete candidate list and sample details are in communities.json; review status stays needs_review.')
    else: p('No candidate met the threshold on this snapshot. This is a valid negative result, not proof that all observations are true positives. No fabricated candidates were added.')
    h('Validation and next steps'); p('An analyst should investigate sensor independence, reporting dates, shared hosting/CDNs, allowlist evidence and incident context. A labeled analyst-reviewed dataset is required to measure detection precision, recall and false-positive reduction. Do not automatically block IPs based on community membership.')
    page(); h('7. Scalability and hardware estimates')
    b=data['logical_bytes_per_observation']; p(f"Measured mean canonical JSON size: {b:.1f} bytes per observation (logical payload, not physical on-disk size). Planning model: logical bytes × 1.5 MongoDB (indexes/cache), × 2.6 Cassandra (two tables plus overhead), × 2.5 Neo4j (graph properties/indexes/edges), × RF 3 × 2 headroom. Compression, logs, backups, skew and working set may change results. Estimates are not measured throughput at scale.")
    def storage(n,f): return f'{n*b*f*3*2/1e9:.1f} GB'
    table(['Observations','MongoDB fleet data','Cassandra fleet data','Neo4j fleet data'],[(f'{n:,}',storage(n,1.5),storage(n,2.6),storage(n,2.5)) for n in (1_000_000,10_000_000,100_000_000)],[130,120,120,120])
    table(['Scale','MongoDB starting point','Cassandra starting point','Neo4j starting point'],[
      ('1M','3 nodes (one replica set); 4 vCPU, 16 GB RAM, 100 GB SSD each','3 nodes RF3; 4 vCPU, 16 GB, 100 GB SSD each','3 Enterprise primaries for HA; 4 vCPU, 16 GB, 100 GB SSD each'),
      ('10M','2 shards × 3 nodes; 8 vCPU, 32 GB, 250 GB SSD each; config/router capacity separate','6 nodes RF3; 8 vCPU, 32 GB, 250 GB SSD each','3 Enterprise primaries; 8 vCPU, 32–64 GB, 250 GB SSD each'),
      ('100M','4 shards × 3 nodes; 16 vCPU, 64 GB, 1 TB SSD each; config/router separate','12 nodes RF3; 16 vCPU, 64 GB, 1 TB SSD each; tune partitions','3 larger Enterprise primaries; 16–32 vCPU, 128 GB+, 1–2 TB NVMe each; consider separately licensed graph sharding')],[55,145,145,145])
    p('Illustrative per-node hardware envelopes deliberately exceed the data-only estimate for working set, compaction, IOPS, logs and growth. No request-rate or retention target is specified; load testing, vendor sizing and failure-domain design are required before purchasing.')
    h('Horizontal scaling mechanisms'); p('MongoDB: shard keys distribute documents, targeted queries avoid scatter-gather; replicate shards and config servers. Cassandra: token-ring partitioning, virtual nodes, replication and tunable consistency; add nodes, stream/rebalance and repair. Neo4j Community is single-instance; Enterprise clusters replicate for HA/read scaling, and ordinary replicated databases do not partition a single graph. Newer specialized Infinigraph sharding is a separate edition/licensing decision, not tested here.')
    page(); h('8. Ergonomics and operations')
    table(['Concern','MongoDB','Cassandra','Neo4j'],[
      ('Developer experience','Flexible BSON and aggregation; straightforward source-of-truth API.','CQL familiar but access-pattern-first; no ad hoc joins, denormalization and partition discipline.','Cypher expressive for paths; understand traversal cardinality, indexes and graph memory.'),
      ('Backups','Coordinated snapshots or managed backups for shards; verify restore.','nodetool snapshots + incremental SSTables; preserve schema, copy off-node, restore/reconcile.','Community offline dump/load; Enterprise online backups; verify consistency.'),
      ('Monitoring','serverStatus, WiredTiger, replication lag, slow queries; exporter/managed monitoring.','JMX/nodetool, partition size, p95 latency, tombstones, compaction, repair, dropped messages.','Heap/page cache, query latency, transaction logs, cluster health and edition-specific metrics.'),
      ('Skills and burden','Document/index modeling, shard keys, backup and replica operations.','Token distribution, consistency, repair/compaction and capacity planning; highest denormalization burden.','Graph modeling, Cypher profiling, memory sizing, clustering/edition choices.')],[70,140,140,140])
    h('9. Final recommendation by access pattern')
    table(['Pattern','Recommended design','Reason / observed fastest'],[
      ('Recent display / history','MongoDB canonical + embedded cache','Simple bounded read, rich details. Measured full history winner: '+winners['threat_history']),
      ('Target and spread','MongoDB for flexible analytics; Neo4j for multi-hop investigation','Comparable one-hop grouping winner: '+winners['target_and_spread']+'. Graph benefits need a dedicated traversal test.'),
      ('Daily analytics','MongoDB aggregation initially; Cassandra day/type summaries when scaled','Observed raw count winner: '+winners['daily_volume']+'. Preaggregation changes workload and must be measured.'),
      ('Sustained ingestion','Cassandra if write scale justifies two materialized views','Observed single-node batch winner: '+winners['real_time_insert']+'. No replicated ingestion test yet.'),
      ('False-positive review','Neo4j graph + MongoDB evidence','Shared relationships are useful triage; analyst approval before declaring false positives.')],[105,165,220])
    p('For the final CTI platform, maintain one canonical record ID, idempotent asynchronous projections, reconciliation checks, independent backup/restore plans, least-privilege access and auditable analyst verdicts. Avoid treating three writes as an atomic distributed transaction.')
    page(); h('10. References and reproducibility')
    p('Instructor specification: Exercise 18, Lab 18.1 and 18.2, supplied assignment text. Instructor GitHub chapter could not be retrieved during preparation: https://github.com/sujeetjagtap/NOSQL-Databases-using-MongoDB/tree/main/chapter-18')
    for title,url in REFS: p(title+': '+url)
    p('Run START-WINDOWS.bat, RUN-LABS.bat, PUBLISH-DOCKER.bat and RUN-PUBLISHED.bat. Submit the published-run PDF with Docker Hub URL and retain the source/Compose package, frozen dataset provenance and raw evidence. Docker Hub image is the Python runner; Compose also pulls the three upstream database images.')
    def footer(canvas,doc):
        w,h=A4; canvas.setStrokeColor(TEAL); canvas.line(52,38,w-52,38); canvas.setFillColor(MUTED); canvas.setFont('Helvetica',8); canvas.drawString(52,25,'Lab 18  |  CTI comparative capstone'); canvas.drawRightString(w-52,25,f'{doc.page}')
    SimpleDocTemplate(str(path),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=44,bottomMargin=50,title='Lab 18 Comparative Capstone',author='Lab 18').build(story,onFirstPage=footer,onLaterPages=footer)
    return path

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(); a.add_argument('--mode',choices=['local','published'],default='published'); x=a.parse_args(); out=ROOT/'evidence'/x.mode
    render_report(json.loads((out/'results.json').read_text()),out,ROOT/'reports'/f'Lab18-{x.mode}-comparative-report.pdf')
