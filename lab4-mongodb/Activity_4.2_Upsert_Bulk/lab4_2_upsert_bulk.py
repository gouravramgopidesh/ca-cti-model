"""Activity 4.2: SKU upsert and five UpdateOne operations in one bulk_write."""

from pathlib import Path
from pymongo import UpdateOne
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab4_common import connect, read_json, seed

CONFIG = Path(__file__).with_name("bulk_operations.json")

SEED = (
    Path(__file__).parent.parent
    / "Activity_4.1_Product_Query_API"
    / "products.json"
)


def upsert_sku(products, sku, price):
    return products.update_one(
        {"sku": sku},
        {
            "$set": {
                "price": price
            },
            "$setOnInsert": {
                "sku": sku,
                "name": f"New product {sku}",
                "stock": 0,
                "tags": ["new"],
                "is_active": True,
            },
        },
        upsert=True,
    )


def main():
    client, products = connect()

    try:
        # Insert initial product data
        seed(products, SEED)

        # Load bulk operation settings
        config = read_json(CONFIG)

        # Update existing product
        updated = upsert_sku(
            products,
            config["existing_sku"],
            config["updated_price"],
        )

        # Insert a new product if its SKU does not exist
        inserted = upsert_sku(
            products,
            config["new_sku"],
            config["new_price"],
        )

        # FIX: UpdateResult uses upserted_id, not upserted_count
        print(
            f"Existing SKU modified={updated.modified_count}; "
            f"new SKU upserted={int(inserted.upserted_id is not None)}"
        )

        # Verify updated price
        assert (
            products.find_one(
                {"sku": config["existing_sku"]}
            )["price"]
            == config["updated_price"]
        )

        # Verify new SKU exists exactly once
        assert products.count_documents(
            {"sku": config["new_sku"]}
        ) == 1

        # Get SKUs for bulk modifications
        increases = config["stock_increment_skus"]
        deactivations = config["deactivate_skus"]

        # Record original stock values
        before_stock = {
            sku: products.find_one({"sku": sku})["stock"]
            for sku in increases
        }

        # Increase stock by 10 for products A, B and C
        requests = [
            UpdateOne(
                {"sku": sku},
                {"$inc": {"stock": 10}},
            )
            for sku in increases
        ]

        # Set is_active=False for products D and E
        requests += [
            UpdateOne(
                {"sku": sku},
                {"$set": {"is_active": False}},
            )
            for sku in deactivations
        ]

        # Confirm exactly five operations
        assert len(requests) == 5

        # Execute bulk operations
        result = products.bulk_write(
            requests,
            ordered=True,
        )

        print(
            f"Bulk write matched={result.matched_count}, "
            f"modified={result.modified_count}, "
            f"upserted={result.upserted_count}"
        )

        # Verify all five documents matched
        assert result.matched_count == 5

        # Verify stock increments
        for sku in increases:
            assert (
                products.find_one({"sku": sku})["stock"]
                == before_stock[sku] + 10
            )

        # Verify products D and E are inactive
        for sku in deactivations:
            assert (
                products.find_one({"sku": sku})["is_active"]
                is False
            )

        print(
            "Five updates verified "
            "(stock A/B/C +10; D/E inactive): PASS"
        )

        print("ACTIVITY 4.2: PASS")

    finally:
        client.close()


if __name__ == "__main__":
    main()