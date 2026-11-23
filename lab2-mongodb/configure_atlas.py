from pathlib import Path
from getpass import getpass
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import PyMongoError

root = Path(__file__).resolve().parent
host = input('Atlas cluster hostname [gourav23.5mr9toc.mongodb.net]: ').strip() or 'gourav23.5mr9toc.mongodb.net'
if not host.endswith('.mongodb.net') or any(c in host for c in '/:@ '):
    raise SystemExit('Enter only the Atlas hostname, not the URI.')
user = input('Atlas database username: ').strip()
password = getpass('Atlas database password (hidden): ')
if not user or not password:
    raise SystemExit('Username and password required.')
uri = f'mongodb+srv://{quote_plus(user)}:{quote_plus(password)}@{host}/?authSource=admin&retryWrites=true&w=majority'
try:
    with MongoClient(uri, serverSelectionTimeoutMS=15000) as client:
        client.admin.command('ping')
except PyMongoError as exc:
    raise SystemExit(f'Atlas connection failed: {type(exc).__name__}. Check database user/password and IP access. No credentials saved.')
(root / '.env').write_text('MONGO_URI_ATLAS=' + uri + '\n', encoding='utf-8')
print('Atlas ping PASSED. Configuration saved privately.')
