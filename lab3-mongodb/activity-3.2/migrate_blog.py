import sys
from pathlib import Path
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import db, export

posts, comments, embedded = db.posts, db.comments, db.posts_embedded
for c in (posts, comments, embedded):
    c.drop()
posts.insert_many([{'_id': i, 'title': title, 'body': 'Introduction to ' + title}
    for i, title in enumerate(['MongoDB', 'Schema Design', 'Python',
                              'Aggregation', 'Indexing'], 1)])
comments.insert_many([{'_id': i, 'post_id': (i-1)//2+1,
    'author': 'Reader ' + str(i), 'text': 'Comment ' + str(i)}
    for i in range(1, 11)])
comments.create_index('post_id')
lookup = {'$lookup': {'from': 'comments', 'localField': '_id',
                      'foreignField': 'post_id', 'as': 'comments'}}
joined = list(posts.aggregate([{'$match': {'_id': 1}}, lookup]))[0]
print('Referenced $lookup:', joined)
list(posts.aggregate([lookup, {'$merge': {'into': 'posts_embedded',
    'whenMatched': 'replace', 'whenNotMatched': 'insert'}}]))
assert posts.count_documents({}) == 5 and comments.count_documents({}) == 10
assert embedded.count_documents({}) == 5
for p in embedded.find():
    expected = list(comments.find({'post_id': p['_id']}))
    assert sorted(p['comments'], key=lambda d: d['_id']) == sorted(expected, key=lambda d: d['_id'])
print('Migration verified: 5 posts and all 10 comments preserved')

def two_reads():
    p = posts.find_one({'_id': 1})
    p['comments'] = list(comments.find({'post_id': 1}))
    return p

def one_lookup():
    return list(posts.aggregate([{'$match': {'_id': 1}}, lookup]))[0]

def one_embedded():
    return embedded.find_one({'_id': 1})

for name, fn, count in [('Referenced separate reads', two_reads, 2),
                        ('Referenced $lookup', one_lookup, 1),
                        ('Embedded find_one', one_embedded, 1)]:
    assert sorted(fn()['comments'], key=lambda d: d['_id']) == sorted(joined['comments'], key=lambda d: d['_id'])
    start = perf_counter()
    for _ in range(30):
        fn()
    print(f'{name}: {count} logical read queries; mean {(perf_counter()-start)*1000/30:.3f} ms (30 runs)')
print('Lookup is one query too, but performs a server-side join.')
print('Timings are illustrative local measurements, not a universal speed ranking.')
export(__file__, list(embedded.find().sort('_id', 1)))
print('LAB 3.2 PASSED')
