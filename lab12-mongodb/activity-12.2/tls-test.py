import subprocess, ssl, socket
from common import *
from pymongo.errors import ServerSelectionTimeoutError

opts = dict(tls=True, tlsCAFile='/client-certs/ca.crt', tlsCertificateKeyFile='/client-certs/client.pem')
with admin('mongo-tls', **opts) as a:
    d=a[DB]
    d.tls_test.replace_one({'_id': 1}, {'_id': 1, 'message': 'Encrypted training record'}, upsert=True)
    doc=d.tls_test.find_one({'_id': 1})
    assert doc and doc['message']=='Encrypted training record'
    assert a.admin.command('getCmdLineOpts')['parsed']['net']['tls']['mode']=='requireTLS'
ctx=ssl.create_default_context(cafile=opts['tlsCAFile'])
ctx.load_cert_chain(opts['tlsCertificateKeyFile'])
with socket.create_connection(('mongo-tls',27017),timeout=5) as sock:
    with ctx.wrap_socket(sock,server_hostname='mongo-tls') as s:
        protocol=s.version(); cipher=s.cipher()[0]; peer=s.getpeercert()
results=[{'test':'authenticated encrypted find','passed':True,'document':doc,'protocol':protocol,'cipher':cipher,'server_certificate':peer}]
for label, options in [('plaintext',{}),('TLS without client certificate',{'tls':True,'tlsCAFile':opts['tlsCAFile']})]:
    try:
        with admin('mongo-tls', **options) as a:
            a[DB].tls_test.find_one()
    except ServerSelectionTimeoutError as e:
        results.append({'test':label,'rejected':True,'passed':True,'error':str(e)})
        print('REJECTED:',label)
    else:
        raise AssertionError('Unexpected connection: '+label)
with admin('mongo-tls', **opts) as a:
    assert a[DB].tls_test.find_one({'_id':1})
chain=subprocess.check_output(['openssl','x509','-in',opts['tlsCertificateKeyFile'],'-noout','-subject','-issuer','-dates','-fingerprint','-sha256'],text=True)
ca=subprocess.check_output(['openssl','x509','-in',opts['tlsCAFile'],'-noout','-subject','-issuer','-dates','-fingerprint','-sha256'],text=True)
save('12.2-tls.json',{'passed':True,'tests':results,'client_certificate':chain,'ca_certificate':ca})
