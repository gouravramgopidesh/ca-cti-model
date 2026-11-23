import os, requests
from common import *
import rag,benchmark

def main():
    url=os.getenv('OLLAMA_URL','http://ollama:11434'); model_name=os.getenv('LLM_MODEL','qwen2.5:0.5b')
    print('Ensuring local LLM is downloaded:',model_name,flush=True)
    with requests.post(url+'/api/pull',json={'model':model_name,'stream':True},stream=True,timeout=(15,900)) as r:
        r.raise_for_status(); last=None
        for line in r.iter_lines():
            if line:
                import json
                d=json.loads(line)
                if 'error' in d: raise RuntimeError(d['error'])
                if d.get('status')!=last: last=d.get('status'); print(last,flush=True)
        assert last=='success'
    print('Loading embedding model (first run downloads weights)...',flush=True)
    model=encoder()
    with connect() as client:
        rag.run(client,model)
        # Release LLM memory before the benchmark.
        requests.post(url+'/api/generate',json={'model':model_name,'keep_alive':0,'stream':False},timeout=60).raise_for_status()
        benchmark.run(client,model)
    print('LAB 17 PASSED: 17.1 and 17.2')
if __name__=='__main__': main()
