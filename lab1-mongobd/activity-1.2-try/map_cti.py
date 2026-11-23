"""1.2 | Try it yourself: CTI. Stores and verifies the classification in MongoDB."""
import json
import os
from pathlib import Path
from pymongo import MongoClient

COLLECTION = 'map_cti'
# Read the matching, editable JSON dataset packaged with this activity.
path = Path(__file__).with_suffix(".json")
rows = json.loads(path.read_text(encoding="utf-8"))

with MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"),
                 serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")
    collection = client["lab1-mongodb"][COLLECTION]
    for row in rows:
        collection.replace_one({"_id": row["_id"]}, row, upsert=True)
    collection.delete_many({"_id": {"$nin": [r["_id"] for r in rows]}})
    actual = list(collection.find().sort("_id", 1))
    assert actual == sorted(rows, key=lambda r: r["_id"])
    path.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    print('1.2 | Try it yourself: CTI')
    print("MongoDB collection:", collection.full_name)
    for row in actual:
        print("-" * 64)
        for key, value in row.items():
            if key != "_id":
                print(f"{key.replace('_', ' ').title()}: {value}")
    print(f"PASS: {len(actual)} documents stored, read back and exported.")
