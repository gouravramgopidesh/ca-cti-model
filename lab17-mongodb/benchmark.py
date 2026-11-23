import csv,time,uuid,os
import numpy as np
import faiss
from common import *

def corpus():
    # Reproducible synthetic natural-language sentences, not Wikipedia quotations.
    topics=['astronomy','botany','geology','history','music','mathematics','medicine','computing','economics','ecology','architecture','linguistics','chemistry','physics','agriculture','transport','literature','oceanography','meteorology','education']
    actions=['examines','describes','compares','measures','documents','models','investigates','explains','classifies','evaluates']
    aspects=['historical records','regional variation','experimental methods','observed changes','practical applications','theoretical foundations','environmental effects','measurement uncertainty','long term trends','published evidence']
    settings=['in a coastal region','during a field study','in a laboratory','across several communities','over a decade']
    return [f'A study of {t} {a} {b} {s}.' for t in topics for a in actions for b in aspects for s in settings][:5000]

def run(client,model):
    faiss.omp_set_num_threads(2)
    texts=corpus(); assert len(texts)==5000 and len(set(texts))==5000
    db=client[DB]; name='benchmark_'+uuid.uuid4().hex[:12]; col=db[name]
    print('Embedding 5000 natural-language sentences...')
    vec=embed(model,texts)
    for i in range(0,5000,500):
        col.insert_many([{'_id':j,'text':texts[j],'source':'synthetic benchmark corpus','embedding':vec[j].tolist()} for j in range(i,i+500)])
        print('Inserted',i+500)
    assert col.count_documents({})==5000
    # Read back from the same MongoDB collection for both FAISS indexes.
    data=np.ascontiguousarray([d['embedding'] for d in col.find({}, {'embedding':1}).sort('_id',1)],dtype='float32')
    assert np.allclose(data,vec)
    rng=np.random.default_rng(17); qids=rng.choice(len(data),100,replace=False); queries=data[qids].copy()
    exact_scores=queries@data.T
    truth=np.argsort(-exact_scores,axis=1,kind='stable')[:,:20]
    rows=[]; details=[]
    def evaluate(kind,params,build,searcher):
        lat=[]; rec=[]
        for i,q in enumerate(queries):
            t=time.perf_counter(); ids=searcher(q); lat.append((time.perf_counter()-t)*1000)
            assert len(ids)==20 and len(set(ids))==20 and min(ids)>=0
            rec.append(len(set(ids)&set(truth[i]))/20)
            details.append({'index':kind,'parameters':params,'query_id':int(qids[i]),'latency_ms':lat[-1],'recall_at_20':rec[-1]})
        row={'index':kind,'parameters':params,'build_seconds':build,'avg_latency_ms':float(np.mean(lat)),'recall_percent':float(np.mean(rec)*100),'queries':100}
        rows.append(row); print(row)
    # Native MongoDB HNSW baseline on the same collection, plus FAISS controlled sweeps.
    build,new=index_ready(col); assert new
    deadline=time.monotonic()+180
    while True:
        hits=search(col,data[0],20,400)
        if len(hits)==20 and any(h['_id']==0 for h in hits): break
        if time.monotonic()>deadline: raise TimeoutError('Benchmark index not synchronized')
        time.sleep(2)
    for candidates in (50,100,200,400):
        evaluate('MongoDB HNSW',f'numCandidates={candidates}',build,lambda q,c=candidates:[h['_id'] for h in search(col,q,20,c)])
    for m in (8,16,32):
        for efc in (32,64,128,256):
            t=time.perf_counter(); idx=faiss.IndexHNSWFlat(DIM,m,faiss.METRIC_INNER_PRODUCT); idx.hnsw.efConstruction=efc; idx.add(data); build=time.perf_counter()-t
            for efs in (32,64,128):
                idx.hnsw.efSearch=efs
                evaluate('FAISS HNSW',f'M={m};efConstruction={efc};efSearch={efs}',build,lambda q:idx.search(q[None,:],20)[1][0].tolist())
    for nlist in (50,100,200):
        t=time.perf_counter(); idx=faiss.IndexIVFFlat(faiss.IndexFlatIP(DIM),DIM,nlist,faiss.METRIC_INNER_PRODUCT); idx.cp.seed=17; idx.train(data); idx.add(data); build=time.perf_counter()-t
        for nprobe in sorted({min(nlist,p) for p in (10,50,100,nlist)}):
            idx.nprobe=nprobe
            evaluate('FAISS IVF',f'nlist={nlist};nprobe={nprobe}',build,lambda q:idx.search(q[None,:],20)[1][0].tolist())
        assert rows[-1]['recall_percent']>=99.0, 'Full-probe IVF should match exact search (ties possible)'
    for filename,records in [('benchmark.csv',rows),('query_details.csv',details)]:
        with (E/filename).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=records[0].keys()); w.writeheader(); w.writerows(records)
    save('benchmark.json',{'collection':col.full_name,'documents':5000,'dimensions':DIM,'queries':100,'top_k':20,'seed':17,'corpus':'synthetic sentences','rows':rows,'native_index_definition':list(col.list_search_indexes())})
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5))
    for kind in ('MongoDB HNSW','FAISS HNSW','FAISS IVF'):
        group=[r for r in rows if r['index']==kind]; ax.scatter([r['avg_latency_ms'] for r in group],[r['recall_percent'] for r in group],label=kind,alpha=.75)
        # Pareto frontier connects only non-dominated points.
        best=-1; front=[]
        for r in sorted(group,key=lambda r:r['avg_latency_ms']):
            if r['recall_percent']>best: front.append(r); best=r['recall_percent']
        ax.plot([r['avg_latency_ms'] for r in front],[r['recall_percent'] for r in front],alpha=.65)
    ax.set_xscale('log'); ax.set(xlabel='Mean query latency (ms, log scale)',ylabel='Recall@20 (%)',title='Lab 17.2 | Latency–recall trade-off'); ax.legend(); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(E/'latency_recall.png',dpi=160); fig.savefig(E/'latency_recall.svg'); plt.close(fig)
    lines=['# Measured index recommendations','',f'Collection: `{col.full_name}`. 5,000 vectors, 384 dimensions, 100 queries.','']
    for kind in ('MongoDB HNSW','FAISS HNSW','FAISS IVF'):
        group=[r for r in rows if r['index']==kind]; fastest=min(group,key=lambda r:r['avg_latency_ms']); best=max(group,key=lambda r:r['recall_percent']); lines += [f'- {kind}: fastest {fastest["avg_latency_ms"]:.3f} ms at {fastest["recall_percent"]:.2f}% recall ({fastest["parameters"]}); highest recall {best["recall_percent"]:.2f}% ({best["parameters"]}).']
    lines+=['','HNSW is a candidate for high-recall RAG; tune search breadth and memory. IVF is useful when an external index is acceptable and probing can be tuned. Full probing costs more; flat exact search is another option for small collections. Select configurations using measured recall targets, not assumed rankings. Native MongoDB timings include network and BSON retrieval; FAISS timings are in-process, so they are not equivalent end-to-end timings. This small synthetic corpus does not establish million-vector performance or memory savings.']
    (E/'recommendations.md').write_text('\n'.join(lines),encoding='utf-8')
    print('LAB 17.2 PASSED: 5000 vectors, native HNSW and FAISS HNSW/IVF, 100 queries per configuration, recall and chart')
