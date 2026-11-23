// Executed equivalent in databases.py. Dedicated lab database only.
db = db.getSiblingDB('lab18_capstone');
db.full_threats.createIndex({id:1},{unique:true});
db.full_threats.createIndex({from_source:1,timestamp:-1,id:1});
db.full_threats.createIndex({threat_type:1,day:1});
db.full_threats.createIndex({day:1});
// threats: {_id: source, from_source: source, recent_threats: [last 50 full rows]}
