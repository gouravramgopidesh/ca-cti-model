"""Idempotent ingestion from Lab7 CTI data plus explicitly supplied course material.
Usage: docker compose exec chatbot python ingest.py
Place real lab texts under chatbot/knowledge/lab01/ ... lab18/ then rerun.
"""
import os,re,hashlib,time
from pathlib import Path
from pymongo import MongoClient,UpdateOne
import httpx
from pypdf import PdfReader

URI=os.getenv('MONGO_URI','mongodb://mongo:27017')
DB=os.getenv('MONGO_DB','lab7-mongodb')
OLLAMA=os.getenv('OLLAMA_URL','http://ollama:11434').rstrip('/')
EMBED=os.getenv('EMBED_MODEL','all-minilm')
client=MongoClient(URI,serverSelectionTimeoutMS=10000)
db=client[DB]; coll=db.chat_knowledge
coll.create_index('source_id',unique=True)

def chunks(text, size=1100, overlap=180):
    text=re.sub(r'\s+',' ',text).strip()
    step=size-overlap
    return [text[i:i+size] for i in range(0,len(text),step) if text[i:i+size].strip()]

def embedding(text):
    try:
        r=httpx.post(f'{OLLAMA}/api/embed',json={'model':EMBED,'input':text},timeout=90)
        r.raise_for_status();return r.json()['embeddings'][0]
    except Exception as exc:
        print('Embedding skipped (run ollama pull all-minilm):',exc)
        return None

def add(id,title,text,typ,url='',lab=None):
    parts=chunks(str(text))
    for j,part in enumerate(parts):
        key=f'{id}:{j}';h=hashlib.sha256(part.encode()).hexdigest()
        existing=coll.find_one({'source_id':key},{'hash':1,'embedding':1})
        if existing and existing.get('hash')==h and existing.get('embedding'):continue
        emb=embedding(part) if not(existing and existing.get('hash')==h) else existing.get('embedding')
        record={'source_id':key,'title':title,'text':part,'source_type':typ,'source_url':url,'hash':h,'lab':lab,'updated_at':time.time()}
        if emb:record['embedding']=emb
        coll.update_one({'source_id':key},{'$set':record},upsert=True)
    return len(parts)

def main():
    total=0
    for collection in ['articles','annualReports','indicators']:
        for d in db[collection].find({}).limit(2500):
            title=str(d.get('title') or d.get('value') or collection)
            text=' '.join(str(d.get(k,'')) for k in ['title','summary','description','category','severity','classification','value','sourceName','tags'])
            if not text.strip():continue
            total+=add(f'lab7:{collection}:{d["_id"]}',title,text,collection,str(d.get('canonicalUrl') or d.get('url') or ''),7)
    root=Path('/app/knowledge')
    for file in root.glob('lab*/*'):
        if file.is_file() and file.suffix.lower() in ('.md','.txt','.pdf'):
            try:
                if file.suffix.lower()=='.pdf':text='\n'.join(p.extract_text() or '' for p in PdfReader(str(file)).pages)
                else:text=file.read_text(encoding='utf-8')
                number=int(re.search(r'lab(\d+)',str(file.parent.name),re.I).group(1))
                total+=add(f'lab{number:02d}:{file.name}',file.name,text,'lab-document',f'local:{file.relative_to(root)}',number)
            except Exception as e:print('Skipped file',file,e)
    print(f'Ingestion completed; processed {total} chunks; stored collection={coll.count_documents({})}.')
if __name__=='__main__':main()
