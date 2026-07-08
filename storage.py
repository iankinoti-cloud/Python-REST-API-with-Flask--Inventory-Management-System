"""Simulated data storage for the inventory.

The "database" is a plain in-memory list of dicts. Every item carries an
auto-incrementing integer ``id``. Seed data mirrors real products from the
OpenFoodFacts database, so the same barcodes can be looked up live through
the external API routes.
"""

import copy

SEED_ITEMS = [
    {
        "id": 1,
        "barcode": "3017620422003",
        "name": "Nutella",
        "brand": "Ferrero",
        "category": "Spreads",
        "price": 850.0,
        "quantity": 24,
        "image_url": "https://images.openfoodfacts.org/images/products/301/762/042/2003/front_en.jpg",
        "nutriscore": "e",
        "source": "openfoodfacts",
    },
    {
        "id": 2,
        "barcode": "5449000000996",
        "name": "Coca-Cola",
        "brand": "Coca-Cola",
        "category": "Beverages",
        "price": 80.0,
        "quantity": 120,
        "image_url": "https://images.openfoodfacts.org/images/products/544/900/000/0996/front_en.jpg",
        "nutriscore": "e",
        "source": "openfoodfacts",
    },
    {
        "id": 3,
        "barcode": "8076809513388",
        "name": "Pesto alla Genovese",
        "brand": "Barilla",
        "category": "Sauces",
        "price": 620.0,
        "quantity": 15,
        "image_url": "https://images.openfoodfacts.org/images/products/807/680/951/3388/front_en.jpg",
        "nutriscore": "d",
        "source": "openfoodfacts",
    },
    {
        "id": 4,
        "barcode": "5000159407236",
        "name": "Snickers",
        "brand": "Mars",
        "category": "Snacks",
        "price": 150.0,
        "quantity": 60,
        "image_url": "https://images.openfoodfacts.org/images/products/500/015/940/7236/front_en.jpg",
        "nutriscore": "e",
        "source": "openfoodfacts",
    },
    {
        "id": 5,
        "barcode": "3175680011480",
        "name": "Biscuits Sésame",
        "brand": "Gerblé",
        "category": "Snacks",
        "price": 430.0,
        "quantity": 8,
        "image_url": "https://images.openfoodfacts.org/images/products/317/568/001/1480/front_en.jpg",
        "nutriscore": "b",
        "source": "openfoodfacts",
    },
    {
        "id": 6,
        "barcode": "3228857000852",
        "name": "Pain 100% Mie",
        "brand": "Harrys",
        "category": "Bakery",
        "price": 320.0,
        "quantity": 10,
        "image_url": "https://images.openfoodfacts.org/images/products/322/885/700/0852/front_en.jpg",
        "nutriscore": "a",
        "source": "openfoodfacts",
    },
    {
        "id": 7,
        "barcode": "6161100000017",
        "name": "All Purpose Wheat Flour 2kg",
        "brand": "Exe",
        "category": "Baking",
        "price": 245.0,
        "quantity": 40,
        "image_url": None,
        "nutriscore": None,
        "source": "seed",
    },
    {
        "id": 8,
        "barcode": "6161100000024",
        "name": "Kilimanjaro Drinking Water 1L",
        "brand": "Kilimanjaro",
        "category": "Beverages",
        "price": 70.0,
        "quantity": 3,
        "image_url": None,
        "nutriscore": None,
        "source": "seed",
    },
]

MUTABLE_FIELDS = {"barcode", "name", "brand", "category", "price", "quantity", "image_url", "nutriscore"}

inventory = []


def reset():
    """Restore the array to its seed state. Used at startup and in tests."""
    inventory.clear()
    inventory.extend(copy.deepcopy(SEED_ITEMS))


def all_items(category=None):
    if category is None:
        return list(inventory)
    return [item for item in inventory if item["category"].lower() == category.lower()]


def get_item(item_id):
    for item in inventory:
        if item["id"] == item_id:
            return item
    return None


def _next_id():
    return max((item["id"] for item in inventory), default=0) + 1


def create_item(data):
    """Append a new item to the array, assigning the next free id."""
    item = {
        "id": _next_id(),
        "barcode": data.get("barcode"),
        "name": data["name"],
        "brand": data.get("brand"),
        "category": data.get("category", "Uncategorized"),
        "price": float(data.get("price", 0)),
        "quantity": int(data.get("quantity", 0)),
        "image_url": data.get("image_url"),
        "nutriscore": data.get("nutriscore"),
        "source": data.get("source", "manual"),
    }
    inventory.append(item)
    return item


def update_item(item_id, changes):
    """Apply a partial update (PATCH semantics) to an existing item."""
    item = get_item(item_id)
    if item is None:
        return None
    for field, value in changes.items():
        if field in MUTABLE_FIELDS:
            item[field] = value
    return item


def delete_item(item_id):
    item = get_item(item_id)
    if item is None:
        return False
    inventory.remove(item)
    return True


def search_items(query):
    """Case-insensitive match against name, brand or barcode."""
    q = query.lower()
    return [
        item
        for item in inventory
        if q in item["name"].lower()
        or (item["brand"] and q in item["brand"].lower())
        or (item["barcode"] and q in item["barcode"])
    ]


def low_stock(threshold=5):
    return [item for item in inventory if item["quantity"] <= threshold]


reset()
