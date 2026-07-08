# Inventory Management System — Flask REST API

Administrator portal backend for an e-commerce website. Employees can
**add, edit, view, and delete** inventory items through a REST API and a
menu-driven CLI, and pull real-time product data from the
[OpenFoodFacts API](https://world.openfoodfacts.org/) to supplement product
details — including importing external products straight into the inventory.

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| API | Flask 3.0 (app factory, JSON error handlers) |
| External HTTP | Requests |
| Storage | Simulated database — in-memory array (`storage.py`) |
| UI | Menu-driven CLI (`cli.py`) talking to the API over HTTP |
| Tests | pytest (82 tests) |
| Dependencies | pipenv, versions pinned in `Pipfile` |

## Quick start

```bash
git clone https://github.com/iankinoti-cloud/Python-REST-API-with-Flask--Inventory-Management-System.git
cd Python-REST-API-with-Flask--Inventory-Management-System
pipenv install --dev

# Terminal 1 — the API
pipenv run python app.py          # http://127.0.0.1:5000

# Terminal 2 — the CLI user interface
pipenv run python cli.py

# Tests
pipenv run pytest
```

## Routes

Full analysis (inputs, outputs, data effects, CLI triggers) in
[docs/route-plan.md](docs/route-plan.md).

### Inventory CRUD (local database array)

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Health check + item count (CLI startup ping) |
| GET | `/items` | List all items, optional `?category=` filter |
| GET | `/items/<id>` | Fetch one item by ID |
| POST | `/items` | Create an item (requires `name`) → 201 |
| PATCH | `/items/<id>` | Partial update of any mutable field |
| DELETE | `/items/<id>` | Remove an item |

### Helper routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/items/search?q=` | Case-insensitive search across name/brand/barcode |
| GET | `/items/low-stock?threshold=` | Items at or below a stock threshold |

### External API (OpenFoodFacts)

| Method | Route | Purpose |
|---|---|---|
| GET | `/external/products/<barcode>` | Live product lookup, normalized to our schema |
| GET | `/external/search?name=` | Live product search by name |
| POST | `/items/import/<barcode>` | Fetch from OpenFoodFacts **and append to the database array** (optional `price`/`quantity` overrides; 409 on duplicate barcode) |

## The CLI

```
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
```

Try option 8 with a seeded barcode, e.g. `3017620422003` (Nutella) —
the data comes back live from OpenFoodFacts. Option 10 imports any barcode
OpenFoodFacts knows into the local inventory with your price and stock.

## The mock database

`storage.py` holds the inventory as a plain Python list. Every item has an
auto-incrementing `id` plus:

```json
{
  "id": 1,
  "barcode": "3017620422003",
  "name": "Nutella",
  "brand": "Ferrero",
  "category": "Spreads",
  "price": 850.0,
  "quantity": 24,
  "image_url": "https://images.openfoodfacts.org/...",
  "nutriscore": "e",
  "source": "openfoodfacts"
}
```

8 seed items mirror real OpenFoodFacts products (Nutella, Coca-Cola,
Barilla Pesto, Snickers, Gerblé, Harrys) plus two Kenyan staples, so
external lookups can be demoed against the same barcodes that sit in the
local array. `source` tracks provenance: `openfoodfacts`, `manual`, or
`seed`.

## Testing

82 tests, one suite per feature:

| Suite | Covers | Approach |
|---|---|---|
| `tests/test_storage.py` | mock database | direct unit tests, parametrized boundaries |
| `tests/test_routes.py` | CRUD + helper routes | real Flask test client, no mocks |
| `tests/test_external_api.py` | OpenFoodFacts client + routes | only `requests.get` mocked |
| `tests/test_cli.py` | CLI end-to-end | real Flask server in a thread, CLI drives it over actual HTTP |

## Git workflow

Built feature-by-feature on branches, merged via pull requests, branches
deleted after merge:

1. `feature/mock-database` → PR #1
2. `feature/crud-routes` → PR #2
3. `feature/external-api` → PR #3
4. `feature/cli` → PR #4
5. `feature/docs` → PR #5
