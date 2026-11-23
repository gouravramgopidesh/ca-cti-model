"""Activity 4.1 try-it-yourself: case-insensitive $regex name search."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lab4_common import connect, read_json, seed, show_docs

CONFIG = Path(__file__).with_name('regex_queries.json')
SEED = Path(__file__).parent.parent / 'Activity_4.1_Product_Query_API' / 'products.json'

def name_search(products, search_string):
    # Escape user-supplied text so special regex characters are treated literally.
    return products.find({'name': {'$regex': re.escape(search_string), '$options': 'i'}}, {'_id': 0})

def main():
    client, products = connect()
    try:
        seed(products, SEED)
        term = read_json(CONFIG)['search_term']
        hits = show_docs(f'Case-insensitive search for {term!r}', name_search(products, term.upper()))
        assert hits, 'Expected at least one match from the supplied seed data'
        print(f'Query with mixed-case term {term.upper()!r}: PASS')
        print('ACTIVITY 4.1 TRY IT YOURSELF: PASS')
    finally:
        client.close()

if __name__ == '__main__':
    main()
