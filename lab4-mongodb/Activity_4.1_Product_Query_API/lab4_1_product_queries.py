"""Activity 4.1: validated product CRUD/query API, operators and pagination."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lab4_common import connect, read_json, seed, show_docs

DATA = Path(__file__).with_name('products.json')

def page_products(collection, page: int, page_size: int):
    if page < 1 or page_size < 1:
        raise ValueError('page and page_size must be positive')
    return list(collection.find({}, {'_id': 0}).sort('name', 1).skip((page - 1) * page_size).limit(page_size))

def main():
    client, products = connect()
    try:
        inserted = seed(products, DATA)
        print(f'Schema validation enabled. Initial products inserted: {inserted}')
        print(f'Collection document count: {products.count_documents({})} (at least 10 required)')
        show_docs('Price between 20 and 50', products.find({'price': {'$gte': 20, '$lte': 50}}, {'_id': 0}))
        show_docs('Out of stock', products.find({'stock': 0}, {'_id': 0}))
        show_docs('Out of stock OR price above 100', products.find({'$or': [{'stock': 0}, {'price': {'$gt': 100}}]}, {'_id': 0}))
        show_docs('In stock AND premium', products.find({'stock': {'$gt': 0}, 'tags': 'premium'}, {'_id': 0}))
        show_docs('Both electronics AND wireless tags', products.find({'tags': {'$all': ['electronics', 'wireless']}}, {'_id': 0}))
        show_docs('Exactly two tags', products.find({'tags': {'$size': 2}}, {'_id': 0}))
        for page in (1, 2, 3):
            rows = page_products(products, page, 5)
            print(f"Page {page} (5 per page, sorted by name): {[row['name'] for row in rows]}")
        sku = 'DEMO-CRUD-01'
        products.update_one({'sku': sku}, {'$setOnInsert': {'sku': sku,'name': 'Demo Adapter','price': 24,'stock': 2,'tags': ['electronics']}}, upsert=True)
        products.update_one({'sku': sku}, {'$set': {'price': 26}})
        assert products.find_one({'sku': sku})['price'] == 26
        products.delete_one({'sku': sku})
        assert products.count_documents({'sku': sku}) == 0
        print('CRUD insert/update/delete demonstration: PASS')
        print('ACTIVITY 4.1: PASS')
    finally:
        client.close()

if __name__ == '__main__':
    main()
