"""Activity 4.2 try-it-yourself: repeatable, duplicate-free bulk import."""
from pathlib import Path
from pymongo import UpdateOne
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lab4_common import connect, read_json

DATA = Path(__file__).with_name('import_products.json')

def import_idempotently(collection, records):
    if not records:
        return None
    return collection.bulk_write([
        UpdateOne({'sku': record['sku']}, {'$set': record}, upsert=True)
        for record in records
    ], ordered=True)

def main():
    client, products = connect()
    try:
        records = read_json(DATA)
        skus = [doc['sku'] for doc in records]
        assert len(skus) == len(set(skus)), 'Incoming file contains duplicate SKUs'
        before = products.count_documents({'sku': {'$in': skus}})
        first = import_idempotently(products, records)
        after_first = products.count_documents({'sku': {'$in': skus}})
        second = import_idempotently(products, records)
        after_second = products.count_documents({'sku': {'$in': skus}})
        print(f'Before import: {before} matching SKUs')
        print(f'First pass upserted={first.upserted_count}, matched={first.matched_count}')
        print(f'Second pass upserted={second.upserted_count}, matched={second.matched_count}')
        print(f'Counts: first={after_first}; second={after_second}; unique input SKUs={len(skus)}')
        assert after_first == after_second == len(skus)
        assert second.upserted_count == 0
        print('Idempotency test (second run creates zero duplicates): PASS')
        print('ACTIVITY 4.2 TRY IT YOURSELF: PASS')
    finally:
        client.close()

if __name__ == '__main__':
    main()
