"""Collect passive public feed observations only; never connect to listed indicators."""
import csv, gzip, hashlib, ipaddress, json, os, re
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from common import *

DATA = ROOT / 'datasets'
MANIFEST = DATA / 'manifest.json'
DATASET = DATA / 'observations.jsonl.gz'
S = requests.Session()
S.headers.update({'User-Agent':'Lab18-academic-CTI/1.0','Accept':'*/*'})
S.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1, status_forcelist=(429,500,502,503,504), respect_retry_after_header=False)))

# Each source is a reporting feed, not necessarily an independent sensor.
STATIC = [
 ('blocklist.de/all','blocklist.de','https://lists.blocklist.de/lists/all.txt','reported_attack','unknown'),
 ('blocklist.de/ssh','blocklist.de','https://lists.blocklist.de/lists/ssh.txt','reported_attack','ssh'),
 ('blocklist.de/mail','blocklist.de','https://lists.blocklist.de/lists/mail.txt','reported_attack','mail'),
 ('blocklist.de/apache','blocklist.de','https://lists.blocklist.de/lists/apache.txt','reported_attack','http'),
 ('blocklist.de/imap','blocklist.de','https://lists.blocklist.de/lists/imap.txt','reported_attack','imap'),
 ('ShadowWhisperer/Threats','ShadowWhisperer','https://raw.githubusercontent.com/ShadowWhisperer/IPs/master/Lists/Threats','exploit_or_malware','unknown'),
 ('romainmarcoux/inbound','romainmarcoux','https://raw.githubusercontent.com/romainmarcoux/malicious-ip/main/full-aa.txt','scanner_or_bruteforce','unknown'),
 ('ThreatHive/blocklist','ThreatHive','https://threathive.net/hiveblocklist.txt','reputation','unknown'),
]

def fetch(url):
    r = S.get(url, timeout=(15,90)); r.raise_for_status()
    if len(r.content) > 40_000_000: raise ValueError('Feed exceeds 40 MB safety cap')
    return r.content

def parse_ips(text):
    """Accept only literal global IPv4/IPv6, optional IPsum occurrence count."""
    seen=set()
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith(('#',';','//')): continue
        fields=re.split(r'[\s,]+',line)
        try: addr=ipaddress.ip_address(fields[0]); count=int(fields[1]) if len(fields)>1 and fields[1].isdigit() else 0
        except (ValueError,IndexError): continue
        if not addr.is_global or addr.is_multicast or addr.is_reserved or addr.is_loopback: continue
        ip=str(addr)
        if ip in seen: continue
        seen.add(ip)
        net=str(ipaddress.ip_network(f'{ip}/{24 if addr.version==4 else 48}',strict=False))
        yield ip,net,count

def make_row(source,publisher,url,kind,target,stamp,basis,ip,net,count):
    day=stamp.date().isoformat()
    key=hashlib.sha256(f'{source}|{day}|{ip}'.encode()).hexdigest()
    return dict(id=key,from_source=source,publisher=publisher,timestamp=int(stamp.timestamp()*1000),day=day,indicator=ip,network=net,threat_type=kind,target=target,source_url=url,source_count=count,timestamp_basis=basis)

def ipsum_specs():
    url='https://api.github.com/repos/stamparm/ipsum/commits'
    try:
        r=S.get(url,params={'path':'ipsum.txt','per_page':15},timeout=(15,45)); r.raise_for_status()
        seen=set(); out=[]
        for c in r.json():
            stamp=datetime.fromisoformat(c['commit']['committer']['date'].replace('Z','+00:00'))
            if stamp > now()+timedelta(hours=1) or now()-stamp>timedelta(days=14) or stamp.date() in seen: continue
            seen.add(stamp.date())
            sha=c['sha']
            out.append(('IPsum/daily','IPsum',f'https://raw.githubusercontent.com/stamparm/ipsum/{sha}/ipsum.txt','reputation','unknown',stamp,'feed_commit_time'))
            if len(out)==3: break
        if out: return out
    except Exception as e: print('IPsum history unavailable:',str(e),flush=True)
    return [('IPsum/daily','IPsum','https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt','reputation','unknown',None,'retrieval_time')]

def validate_cache():
    if not MANIFEST.exists() or not DATASET.exists(): return None
    m=json.loads(MANIFEST.read_text())
    with gzip.open(DATASET,'rt',encoding='utf-8') as f: rows=[json.loads(line) for line in f]
    if len(rows)!=TOTAL+HOLDOUT or len({r['id'] for r in rows})!=len(rows) or digest(rows)!=m['dataset_sha256'] or digest(rows[:TOTAL])!=m['baseline_sha256'] or hashlib.sha256(DATASET.read_bytes()).hexdigest()!=m['compressed_sha256'] or len({r['publisher'] for r in rows[:TOTAL]})<2:
        raise RuntimeError('Frozen dataset failed integrity check. Preserve it; move manifest and observations files aside to recollect.')
    print('Reusing frozen verified dataset:',m['dataset_sha256'],flush=True)
    return rows,m

def collect():
    DATA.mkdir(exist_ok=True)
    cached=validate_cache()
    if cached: return cached
    groups=[]; provenance=[]; errors=[]; global_ids=set()
    specs=ipsum_specs()+[(*s,None,'retrieval_time') for s in STATIC]
    for source,publisher,url,kind,target,stamp,basis in specs:
        try:
            raw=fetch(url); retrieved=now(); stamp=stamp or retrieved
            # Only current snapshots or genuine dated historical versions are accepted.
            rows=[]
            for ip,net,count in parse_ips(raw.decode('utf-8-sig',errors='replace')):
                row=make_row(source,publisher,url,kind,target,stamp,basis,ip,net,count)
                if row['id'] in global_ids: continue
                global_ids.add(row['id']); rows.append(row)
                if len(rows)>=150_000: break
            if not rows: raise ValueError('No valid public IP observations parsed')
            # Retain original order (some feeds rank by occurrence); sample deterministically by round-robin.
            groups.append(deque(rows)); provenance.append(dict(source=source,publisher=publisher,url=url,feed_time=stamp.isoformat(),retrieved_at=retrieved.isoformat(),timestamp_basis=basis,parsed_capped=len(rows),sha256=hashlib.sha256(raw).hexdigest()))
            print(f'Collected {source} {stamp.date()}: {len(rows):,} observations',flush=True)
        except Exception as e:
            errors.append(dict(source=source,url=url,error=str(e))); print(f'Feed unavailable: {source}: {e}',flush=True)
    rows=[]
    # Round robin, ensuring smaller feeds are represented rather than using a single huge source.
    while groups and len(rows)<TOTAL+HOLDOUT:
        active=[]
        for g in groups:
            if g and len(rows)<TOTAL+HOLDOUT: rows.append(g.popleft())
            if g: active.append(g)
        groups=active
    if len(rows)!=TOTAL+HOLDOUT or len({r['publisher'] for r in rows[:TOTAL]})<2:
        dump_json(DATA/'collection-failure.json',dict(available=len(rows),sources=provenance,errors=errors))
        raise RuntimeError(f'Only {len(rows):,} genuine observations available or fewer than two publishers. Need {TOTAL+HOLDOUT:,}; no fake padding. Check Internet and retry.')
    m=dict(collected_at=now().isoformat(),dataset_sha256=digest(rows),baseline_sha256=digest(rows[:TOTAL]),baseline_count=TOTAL,holdout_count=HOLDOUT,distinct_baseline_ips=len({r['indicator'] for r in rows[:TOTAL]}),source_counts=dict(Counter(r['from_source'] for r in rows[:TOTAL])),publisher_counts=dict(Counter(r['publisher'] for r in rows[:TOTAL])),day_counts=dict(sorted(Counter(r['day'] for r in rows[:TOTAL]).items())),sources=provenance,errors=errors,definition='One genuine public feed observation per feed, UTC snapshot day and IP. Multiple reports of an IP are intentionally retained; not a count of unique attacks or confirmed malicious actors.',selection='Round-robin across available feed snapshots in original feed order, capped at 150000 valid observations per snapshot; last 1000 held out for new inserts.')
    with gzip.open(DATASET,'wt',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r,separators=(',',':'))+'\n')
    m['compressed_sha256']=hashlib.sha256(DATASET.read_bytes()).hexdigest()
    dump_json(MANIFEST,m)
    return rows,m

if __name__=='__main__':
    rows,m=collect(); print('Collected and frozen:',len(rows),m['publisher_counts'])
