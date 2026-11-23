import os, subprocess, tempfile, shutil
from pathlib import Path

def cmd(*args):
    subprocess.run(['openssl', *map(str, args)], check=True)

ca, server, client = map(Path, ['/ca-private', '/server-certs', '/client-certs'])
for p in (ca, server, client): p.mkdir(exist_ok=True)
if all(p.exists() for p in (ca/'ca.key', ca/'ca.crt', server/'server.pem', server/'ca.crt', client/'client.pem', client/'ca.crt')):
    print('Existing certificates retained.')
else:
    os.umask(0o077)
    cmd('req','-x509','-newkey','rsa:4096','-nodes','-days','365','-sha256','-keyout',ca/'ca.key','-out',ca/'ca.crt','-subj','/CN=Lab12-Local-CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign')
    for name, dest, ext in [('server',server,'subjectAltName=DNS:mongo-tls,DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth,clientAuth'),('client',client,'extendedKeyUsage=clientAuth')]:
        with tempfile.TemporaryDirectory() as tmp:
            t=Path(tmp)
            (t/'ext').write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\n'+ext+'\n')
            cmd('req','-new','-newkey','rsa:2048','-nodes','-keyout',t/'key','-out',t/'csr','-subj','/CN='+('mongo-tls' if name=='server' else 'lab12-client'))
            cmd('x509','-req','-in',t/'csr','-CA',ca/'ca.crt','-CAkey',ca/'ca.key','-CAcreateserial','-days','365','-sha256','-extfile',t/'ext','-out',t/'crt')
            (dest/(name+'.pem')).write_bytes((t/'key').read_bytes()+(t/'crt').read_bytes())
            shutil.copyfile(ca/'ca.crt',dest/'ca.crt')
            # Official mongo image UID 999; only server gets its private key.
            os.chown(dest/(name+'.pem'),999 if name=='server' else 0,999 if name=='server' else 0)
            os.chmod(dest/(name+'.pem'),0o600)
            os.chmod(dest/'ca.crt',0o644)
for name, dest in [('server',server),('client',client)]:
    cmd('verify','-CAfile',dest/'ca.crt',dest/(name+'.pem'))
print('CA, server and client certificate chain verified.')
