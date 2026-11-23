import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import db, export

# Reference stable course codes, not copies of complete course documents.
# A prerequisite can be shared; updates to its title stay in one place.
source = list(db.courses.find({}, {'_id': 0}))
assert {d['code'] for d in source} == {'CS101', 'CS201', 'CS401'}
links = {'CS101': [], 'CS201': ['CS101'], 'CS401': ['CS201']}
for course in source:
    course['prerequisite_codes'] = links[course['code']]
c = db.courses_prerequisites
c.drop()
c.create_index('code', unique=True)
c.insert_many(source)
result = list(c.aggregate([
    {'$match': {'code': 'CS401'}},
    {'$lookup': {'from': c.name, 'localField': 'prerequisite_codes',
                 'foreignField': 'code', 'as': 'prerequisites'}},
    {'$project': {'_id': 0, 'code': 1, 'prerequisites.code': 1,
                  'prerequisites.title': 1}}]))
print('CS401 direct prerequisites:', result)
assert result[0]['prerequisites'][0]['code'] == 'CS201'
chain = list(c.aggregate([
    {'$match': {'code': 'CS401'}},
    {'$graphLookup': {'from': c.name, 'startWith': '$prerequisite_codes',
        'connectFromField': 'prerequisite_codes', 'connectToField': 'code',
        'as': 'chain'}}]))[0]['chain']
assert {d['code'] for d in chain} == {'CS101', 'CS201'}
print('All prerequisites:', sorted(d['code'] for d in chain))
print('Choice: references avoid duplicated course details and stale titles.')
print('Tradeoff: joins required; application must prevent cycles and dangling codes.')
export(__file__, list(c.find().sort('code', 1)))
print('LAB 3.1 TRY PASSED')
