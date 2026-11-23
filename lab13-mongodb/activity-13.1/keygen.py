import os, secrets
from pathlib import Path
p = Path('/shared/keyfile')
if not p.exists():
    with p.open('x') as f:
        f.write(secrets.token_hex(378))
    print('Generated shared keyfile (756 characters).')
else:
    print('Retained existing shared keyfile.')
os.chmod(p, 0o400)
