import argparse
from common import connect,encoder,DB
from rag import ask
p=argparse.ArgumentParser(); p.add_argument('--user',default='manual-demo'); p.add_argument('question'); a=p.parse_args()
with connect() as c:
    result=ask(c[DB],encoder(),a.user,a.question)
    print(result['answer']); print('Sources:',[(s['source'],s['score']) for s in result['sources']]); print('Previous exchanges:',result['history_exchanges'])
