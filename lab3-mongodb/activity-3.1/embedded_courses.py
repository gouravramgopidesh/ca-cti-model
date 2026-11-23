import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import db, export
from pymongo.errors import WriteError

string = {'bsonType': 'string'}
schema = {'bsonType': 'object', 'required': [
    'title', 'code', 'instructor', 'schedule', 'students'],
    'properties': {
        'title': string, 'code': string, 'instructor': string,
        'schedule': {'bsonType': 'object',
            'required': ['days', 'times', 'room'], 'properties': {
                'days': {'bsonType': 'array', 'items': string},
                'times': string, 'room': string}},
        'students': {'bsonType': 'array', 'items': {
            'bsonType': 'object', 'required': ['name', 'id', 'grade'],
            'properties': {'name': string, 'id': string, 'grade': string}}}}}

courses = [
    ('CS101', 'Programming', 'Dr. Rao', ['Monday', 'Wednesday'],
     '09:00-10:00', 'A101', [('Ananya', 'S01', 'A'), ('Ravi', 'S02', 'B')]),
    ('CS201', 'Data Structures', 'Dr. Mehta', ['Tuesday', 'Thursday'],
     '10:00-11:00', 'B201', [('Ravi', 'S02', 'A'), ('Meera', 'S03', 'B+')]),
    ('CS401', 'Database Systems', 'Dr. Rao', ['Monday', 'Friday'],
     '11:00-12:00', 'C301', [('Meera', 'S03', 'A'), ('Arjun', 'S04', 'A-')])]

db.courses.drop()
c = db.create_collection('courses', validator={'$jsonSchema': schema},
                         validationLevel='strict', validationAction='error')
c.create_index('code', unique=True)
c.insert_many([{'code': code, 'title': title, 'instructor': teacher,
    'schedule': {'days': days, 'times': times, 'room': room},
    'students': [{'name': n, 'id': i, 'grade': g} for n, i, g in roster]}
    for code, title, teacher, days, times, room, roster in courses])
try:
    c.insert_one({'title': 'Invalid course'})
except WriteError as exc:
    assert exc.code == 121
    print('PASS: schema rejected invalid course (code 121)')
else:
    raise AssertionError('Validation did not reject invalid course')
monday = list(c.find({'schedule.days': 'Monday'}, {'_id': 0, 'code': 1, 'title': 1}))
print('Monday courses:', monday)
assert {d['code'] for d in monday} == {'CS101', 'CS401'}
students = list(c.aggregate([
    {'$match': {'instructor': 'Dr. Rao'}}, {'$unwind': '$students'},
    {'$project': {'_id': 0, 'code': 1, 'student': '$students'}}]))
for s in students:
    print('Dr. Rao enrollment:', s)
assert len(students) == 4 and c.count_documents({}) == 3
export(__file__, list(c.find().sort('code', 1)))
print('LAB 3.1 PASSED: 3 courses, 2 Monday courses, 4 enrollments')
