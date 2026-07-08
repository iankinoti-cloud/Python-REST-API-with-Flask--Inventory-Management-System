"""Menu-driven CLI for the Inventory Management API.

Every menu action maps to exactly one API route, so this doubles as living
documentation of when each route is triggered. Run the API first
(``pipenv run python app.py``), then this CLI in another terminal.
"""

import requests

API_URL = "http://127.0.0.1:5000"

MENU = """
========= INVENTORY ADMIN PORTAL =========
 Inventory (local database array)
  1. View all items          GET    /items
  2. View item by ID         GET    /items/<id>
  3. Search inventory        GET    /items/search?q=
  4. Low-stock report        GET    /items/low-stock
  5. Add item manually       POST   /items
  6. Edit item               PATCH  /items/<id>
  7. Delete item             DELETE /items/<id>

 OpenFoodFacts (external API)
  8. Look up barcode         GET    /external/products/<barcode>
  9. Search by product name  GET    /external/search?name=
 10. Import into inventory   POST   /items/import/<barcode>

  0. Exit
===========================================
"""


def fmt_item(item):
    """One readable line per inventory item."""
    price = f"KES {item['price']:,.2f}"
    return (
        f"[{item['id']:>3}] {item['name']:<35} {item.get('brand') or '-':<15} "
        f"{price:>14}  qty: {item['quantity']:>4}  ({item['source']})"
    )


def show_items(items):
    if not items:
        print("  (no items)")
        return
    for item in items:
        print(" " + fmt_item(item))
    print(f"  -- {len(items)} item(s)")


def show_response_error(response):
    try:
        message = response.json().get("error", response.text)
    except ValueError:
        message = response.text
    print(f"  !! {response.status_code}: {message}")


def ask(prompt, default=None, cast=str):
    """Prompt for a value; empty input returns the default."""
    raw = input(prompt).strip()
    if not raw:
        return default
    try:
        return cast(raw)
    except ValueError:
        print(f"  !! '{raw}' is not valid, using {default}")
        return default


# --------------------------------------------------------------- actions


def view_all():
    category = ask("  Filter by category (blank for all): ")
    params = {"category": category} if category else {}
    response = requests.get(f"{API_URL}/items", params=params)
    show_items(response.json())


def view_one():
    item_id = ask("  Item ID: ", cast=int)
    response = requests.get(f"{API_URL}/items/{item_id}")
    if response.status_code == 200:
        for key, value in response.json().items():
            print(f"    {key:>10}: {value}")
    else:
        show_response_error(response)


def search_inventory():
    query = ask("  Search (name/brand/barcode): ", default="")
    response = requests.get(f"{API_URL}/items/search", params={"q": query})
    if response.status_code == 200:
        show_items(response.json())
    else:
        show_response_error(response)


def low_stock_report():
    threshold = ask("  Threshold [5]: ", default=5, cast=int)
    response = requests.get(
        f"{API_URL}/items/low-stock", params={"threshold": threshold}
    )
    show_items(response.json())


def add_item():
    payload = {
        "name": ask("  Name: "),
        "brand": ask("  Brand: "),
        "category": ask("  Category: ", default="Uncategorized"),
        "barcode": ask("  Barcode: "),
        "price": ask("  Price (KES): ", default=0, cast=float),
        "quantity": ask("  Quantity: ", default=0, cast=int),
    }
    response = requests.post(f"{API_URL}/items", json=payload)
    if response.status_code == 201:
        print("  Created:")
        print(" " + fmt_item(response.json()))
    else:
        show_response_error(response)


def edit_item():
    item_id = ask("  Item ID to edit: ", cast=int)
    print("  Leave a field blank to keep its current value.")
    changes = {}
    for field, cast in (
        ("name", str), ("brand", str), ("category", str),
        ("price", float), ("quantity", int),
    ):
        value = ask(f"  New {field}: ", cast=cast)
        if value is not None:
            changes[field] = value
    if not changes:
        print("  Nothing to change.")
        return
    response = requests.patch(f"{API_URL}/items/{item_id}", json=changes)
    if response.status_code == 200:
        print("  Updated:")
        print(" " + fmt_item(response.json()))
    else:
        show_response_error(response)


def delete_item():
    item_id = ask("  Item ID to delete: ", cast=int)
    confirm = ask(f"  Really delete item {item_id}? (y/N): ", default="n")
    if str(confirm).lower() != "y":
        print("  Cancelled.")
        return
    response = requests.delete(f"{API_URL}/items/{item_id}")
    if response.status_code == 200:
        print(f"  Deleted item {item_id}.")
    else:
        show_response_error(response)


def lookup_barcode():
    barcode = ask("  Barcode: ")
    response = requests.get(f"{API_URL}/external/products/{barcode}")
    if response.status_code == 200:
        for key, value in response.json().items():
            print(f"    {key:>10}: {value}")
    else:
        show_response_error(response)


def search_external():
    name = ask("  Product name: ", default="")
    response = requests.get(f"{API_URL}/external/search", params={"name": name})
    if response.status_code != 200:
        show_response_error(response)
        return
    results = response.json()
    if not results:
        print("  (no matches on OpenFoodFacts)")
    for product in results:
        print(
            f"    {product['barcode']:<15} {product['name']:<35} "
            f"{product.get('brand') or '-'}"
        )


def import_barcode():
    barcode = ask("  Barcode to import: ")
    payload = {
        "price": ask("  Selling price (KES) [0]: ", default=0, cast=float),
        "quantity": ask("  Initial stock [0]: ", default=0, cast=int),
    }
    response = requests.post(f"{API_URL}/items/import/{barcode}", json=payload)
    if response.status_code == 201:
        print("  Imported into inventory:")
        print(" " + fmt_item(response.json()))
    else:
        show_response_error(response)


ACTIONS = {
    "1": view_all,
    "2": view_one,
    "3": search_inventory,
    "4": low_stock_report,
    "5": add_item,
    "6": edit_item,
    "7": delete_item,
    "8": lookup_barcode,
    "9": search_external,
    "10": import_barcode,
}


def check_api():
    """Triggered on startup: GET / to confirm the API is reachable."""
    try:
        info = requests.get(f"{API_URL}/", timeout=3).json()
    except requests.RequestException:
        print(f"Cannot reach the API at {API_URL}.")
        print("Start it first: pipenv run python app.py")
        return False
    print(f"Connected to {info['service']} — {info['items_in_stock']} items in stock.")
    return True


def run():
    if not check_api():
        return
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print(f"  !! '{choice}' is not a menu option.")
            continue
        try:
            action()
        except requests.RequestException as exc:
            print(f"  !! API request failed: {exc}")


if __name__ == "__main__":
    run()
