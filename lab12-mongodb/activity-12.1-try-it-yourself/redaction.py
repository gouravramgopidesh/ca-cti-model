import os
from common import *

with admin() as a:
    db = a[DB]
    db.employees.replace_one({'_id': 1}, {'_id': 1, 'name': 'Demo analyst', 'department': 'Security', 'salary': 85000}, upsert=True)
    if 'employees_public' not in db.list_collection_names():
        db.command('create', 'employees_public', viewOn='employees', pipeline=[{'$project': {'salary': 0}}])
    role(db, 'employeePublicReader', 'employees_public', ['find'])
    role(db, 'hrReader', 'employees', ['find'])
    user(db, 'app_user_read', os.environ['LAB12_READ_PASSWORD'], ['reportReader', 'employeePublicReader'])
    user(db, 'app_user_write', os.environ['LAB12_WRITE_PASSWORD'], ['reportWriter', 'employeePublicReader'])
    user(db, 'hr_user', os.environ['LAB12_HR_PASSWORD'], ['hrReader'])
results = []
for username, password_role in [('app_user_read', 'READ'), ('app_user_write', 'WRITE')]:
    with app(username, password_role) as c:
        d = c[DB]
        visible = d.employees_public.find_one({'_id': 1})
        assert visible and 'salary' not in visible
        results.append({'user': username, 'visible': visible, 'salary_hidden': True})
        results.append(denied(username + ' raw employee read', lambda: d.employees.find_one()))
with app('hr_user', 'HR') as c:
    full = c[DB].employees.find_one({'_id': 1})
    assert full and full['salary'] == 85000
    results.append({'user': 'hr_user', 'visible': full, 'salary_visible': True})
save('12.1-redaction.json', {'passed': True, 'tests': results})
