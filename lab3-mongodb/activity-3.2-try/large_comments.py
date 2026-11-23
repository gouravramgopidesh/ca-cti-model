import sys
from pathlib import Path
from bson import BSON
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import db, export

N = 10_000
LIMIT = 16 * 1024 * 1024
posts = db.posts_10000_referenced
comments = db.comments_10000
for c in (posts, comments):
    c.drop()
post = {'_id': 1, 'title': 'Popular post', 'comment_count': N}
posts.insert_one(post)
rows = [{'_id': i, 'post_id': 1, 'author': f'Reader {i}',
         'text': 'Example comment ' + 'x'*200} for i in range(1, N+1)]
comments.insert_many(rows)
comments.create_index([('post_id', 1), ('_id', 1)])
size = len(BSON.encode({**post, 'comments': rows}))
print(f'Hypothetical embedded BSON: {size:,} bytes; limit: {LIMIT:,} bytes')
print('10,000 short comments do not necessarily exceed 16 MiB.')
print('Longer comments or continued growth can exceed the limit.')
print('Large arrays increase read payload and create a hot post document.')
print('Alternative: separate indexed comments, cursor pagination (or bounded buckets).')
page1 = list(comments.find({'post_id': 1}).sort('_id', 1).limit(20))
page2 = list(comments.find({'post_id': 1, '_id': {'$gt': page1[-1]['_id']}})
             .sort('_id', 1).limit(20))
assert comments.count_documents({'post_id': 1}) == N
assert [d['_id'] for d in page1] == list(range(1, 21))
assert [d['_id'] for d in page2] == list(range(21, 41))
print('Stored comments:', N, '| Page 1 IDs: 1-20 | Page 2 IDs: 21-40')
# Export the actual referenced comment collection, not a hypothetical document.
export(__file__, list(comments.find().sort('_id', 1)))
print('LAB 3.2 TRY PASSED')
