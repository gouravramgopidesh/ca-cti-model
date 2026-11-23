import os, time, json
from pathlib import Path
from pymongo import MongoClient
from pymongo.operations import SearchIndexModel
E=Path('evidence'); E.mkdir(exist_ok=True)
DIM=384
MODEL='sentence-transformers/all-MiniLM-L6-v2'
DB='lab17_rag'

def connect():
    c=MongoClient(os.environ.get('MONGO_URI','mongodb://mongo:27017/?directConnection=true'),serverSelectionTimeoutMS=15000)
    c.admin.command('ping'); return c

def encoder():
    from sentence_transformers import SentenceTransformer
    import torch
    torch.set_num_threads(2)
    return SentenceTransformer(MODEL,device='cpu')

def embed(model,texts):
    import numpy as np
    x=np.ascontiguousarray(model.encode(texts,batch_size=64,normalize_embeddings=True,show_progress_bar=False),dtype='float32')
    assert x.shape==(len(texts),DIM) and np.isfinite(x).all()
    return x

def save(name,obj):
    (E/name).write_text(json.dumps(obj,indent=2,default=str),encoding='utf-8')

def index_ready(col,name='vector_index'):
    t=time.perf_counter()
    found=list(col.list_search_indexes(name=name))
    if not found:
        col.create_search_index(SearchIndexModel(name=name,type='vectorSearch',definition={'fields':[{'type':'vector','path':'embedding','numDimensions':DIM,'similarity':'cosine'}]}))
    deadline=time.monotonic()+900
    while time.monotonic()<deadline:
        rows=list(col.list_search_indexes(name=name))
        if rows and rows[0].get('queryable') and rows[0].get('status')=='READY': return time.perf_counter()-t,not bool(found)
        if rows and rows[0].get('status')=='FAILED': raise RuntimeError(str(rows))
        time.sleep(3)
    raise TimeoutError('Vector index not READY: '+name)

def search(col,vector,limit,candidates,name='vector_index'):
    return list(col.aggregate([{'$vectorSearch':{'index':name,'path':'embedding','queryVector':vector.tolist(),'numCandidates':candidates,'limit':limit}},{'$project':{'text':1,'source':1,'score':{'$meta':'vectorSearchScore'}}}]))
