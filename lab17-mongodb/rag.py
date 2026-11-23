import os,time,uuid
from datetime import datetime,timezone
from pathlib import Path
import requests
from common import *

def chunks(text,size=100,overlap=20):
    words=text.split(); out=[]
    for start in range(0,len(words),size-overlap):
        out.append(' '.join(words[start:start+size]))
        if start+size>=len(words): break
    return out

def generate(prompt):
    url=os.getenv('OLLAMA_URL','http://ollama:11434'); model=os.getenv('LLM_MODEL','qwen2.5:0.5b')
    r=requests.post(url+'/api/generate',json={'model':model,'prompt':prompt,'stream':False,'options':{'temperature':0,'num_predict':180,'num_ctx':4096}},timeout=600)
    r.raise_for_status(); data=r.json(); assert data.get('done') and data.get('response','').strip(); return data['response'].strip()

def ask(db,model,user,query):
    mem=db.conversations
    history=list(mem.find({'user_id':user}).sort([('timestamp',-1),('_id',-1)]).limit(10))[::-1]
    retrieval_query=' '.join([m['content'] for m in history if m['role']=='user'][-1:]+[query])
    hits=search(db.documents,embed(model,[retrieval_query])[0],3,20)
    assert len(hits)==3
    context='\n'.join(f'[{i+1}] {h["source"]}: {h["text"]}' for i,h in enumerate(hits))
    prompt=f'Answer using only the documents. Cite source numbers like [1]. If insufficient say so. Documents:\n{context}\nConversation:\n'+ '\n'.join(f'{m["role"]}: {m["content"]}' for m in history)+f'\nQuestion: {query}\nAnswer:'
    t=time.perf_counter(); answer=generate(prompt); elapsed=time.perf_counter()-t
    exchange=uuid.uuid4().hex
    for role,content in [('user',query),('assistant',answer)]:
        mem.insert_one({'user_id':user,'exchange_id':exchange,'timestamp':datetime.now(timezone.utc),'role':role,'content':content})
    return {'query':query,'retrieval_query':retrieval_query,'answer':answer,'sources':hits,'history_messages':len(history),'history_exchanges':len({m['exchange_id'] for m in history}),'prompt':prompt,'generation_seconds':elapsed}

def run(client,model):
    db=client[DB]; col=db.documents
    docs=[]
    for p in sorted(Path('documents').glob('*.txt')):
        for i,text in enumerate(chunks(p.read_text())): docs.append({'_id':f'{p.stem}-{i}','source':p.name,'text':text})
    assert len(docs)>=5 and all(0<len(d['text'].split())<=100 for d in docs)
    vectors=embed(model,[d['text'] for d in docs]);
    for d,v in zip(docs,vectors): d['embedding']=v.tolist(); col.replace_one({'_id':d['_id']},d,upsert=True)
    index_ready(col)
    # Search indexing is asynchronous even when an existing index is READY.
    deadline=time.monotonic()+180
    while True:
        hits=search(col,vectors[0],3,20)
        if len(hits)==3 and hits[0]['_id']==docs[0]['_id']: break
        if time.monotonic()>deadline: raise TimeoutError('RAG index not synchronized')
        time.sleep(2)
    db.conversations.create_index([('user_id',1),('timestamp',-1)])
    user='demo-'+uuid.uuid4().hex; other='other-'+uuid.uuid4().hex
    # Establish five complete exchanges without pretending they were LLM calls.
    # Actual model calls below generate all tested answers; synthetic fixtures only test window bounds.
    for i in range(6):
        for role in ('user','assistant'):
            db.conversations.insert_one({'user_id':user,'exchange_id':f'fixture-{i}','timestamp':datetime(2020,1,1,0,i,0 if role=='user' else 1,tzinfo=timezone.utc),'role':role,'content':f'Memory fixture {i} {role}'})
    first=ask(db,model,user,'What is ransomware and how can defenders recover?')
    second=ask(db,model,user,'What backups should they maintain?')
    isolated=ask(db,model,other,'What is phishing?')
    assert first['history_messages']==10 and first['history_exchanges']==5 and 'Memory fixture 0' not in first['prompt']
    assert second['history_exchanges']==5 and first['answer'] in second['prompt'] and isolated['history_messages']==0
    assert db.conversations.count_documents({'user_id':user,'exchange_id':{'$not':{'$regex':'^fixture-'}}})==4
    assert any(h['source']=='ransomware.txt' for h in first['sources'])
    save('rag.json',{'model':os.getenv('LLM_MODEL','qwen2.5:0.5b'),'embedding_model':MODEL,'chunks':len(docs),'chunk_words':[len(d['text'].split()) for d in docs],'native_vector_search':True,'results':[first,second,isolated],'memory_verified':True,'fixture_exchanges':6})
    for r in (first,second,isolated): print(r['query'], '\n',r['answer'],'\nSources:',[(h['source'],round(h['score'],4)) for h in r['sources']])
    print('LAB 17.1 PASSED: native vector search, real LLM, five-exchange memory and isolation')
