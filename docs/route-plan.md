# Route Plan & Analysis

For every route: what goes in, what comes out, what it changes in the data
array, and when the CLI triggers it. This document was written **before**
implementation and drove the design.

## Inventory CRUD

### `GET /`
- **Inputs:** none
- **Output:** `{"service", "status", "items_in_stock"}` — 200
- **Data change:** none
- **CLI trigger:** automatically on CLI startup, as a connectivity check.
  If it fails, the CLI tells the user to start the API and exits.

### `GET /items`
- **Inputs:** optional query param `category` (case-insensitive)
- **Output:** JSON array of items — 200 (empty array if no matches)
- **Data change:** none
- **CLI trigger:** menu option **1 — View all items** (prompts for an
  optional category filter)

### `GET /items/<id>`
- **Inputs:** integer `id` in the path
- **Output:** the item object — 200; `{"error"}` — 404 if the id is unknown
- **Data change:** none
- **CLI trigger:** menu option **2 — View item by ID**

### `POST /items`
- **Inputs:** JSON body — `name` **(required)**, optional `barcode`,
  `brand`, `category`, `price`, `quantity`
- **Output:** the created item (with its new auto-assigned `id`) — 201;
  `{"error"}` — 400 for a missing body/name or non-numeric price/quantity
- **Data change:** **appends** one item to the array; `id` =
  `max(existing ids) + 1`; `source` defaults to `"manual"`
- **CLI trigger:** menu option **5 — Add item manually** (prompts for each
  field)

### `PATCH /items/<id>`
- **Inputs:** integer `id` in the path + JSON body with any subset of
  `name`, `brand`, `category`, `barcode`, `price`, `quantity`,
  `image_url`, `nutriscore`. `id` and unknown fields are ignored.
- **Output:** the updated item — 200; 404 unknown id; 400 empty body
- **Data change:** **mutates** the matching item in place; untouched
  fields keep their values (PATCH semantics)
- **CLI trigger:** menu option **6 — Edit item** (blank input keeps the
  current value of a field)

### `DELETE /items/<id>`
- **Inputs:** integer `id` in the path
- **Output:** `{"deleted": <id>}` — 200; 404 unknown id
- **Data change:** **removes** the item from the array. Freed ids may be
  reused (next id is always `max + 1`).
- **CLI trigger:** menu option **7 — Delete item**, after a y/N
  confirmation prompt

## Helper routes

### `GET /items/search?q=<query>`
- **Inputs:** query param `q` (required)
- **Output:** array of items whose name, brand or barcode contains the
  query (case-insensitive) — 200; 400 if `q` is missing
- **Data change:** none
- **CLI trigger:** menu option **3 — Search inventory**

### `GET /items/low-stock?threshold=<n>`
- **Inputs:** optional integer `threshold` (default 5)
- **Output:** array of items with `quantity <= threshold` — 200; 400 if
  the threshold is not an integer
- **Data change:** none
- **CLI trigger:** menu option **4 — Low-stock report**

## External API (OpenFoodFacts)

### `GET /external/products/<barcode>`
- **Inputs:** barcode string in the path
- **Output:** normalized product (`barcode`, `name`, `brand`, `category`,
  `image_url`, `nutriscore`, `source: "openfoodfacts"`) — 200;
  404 if OpenFoodFacts doesn't know the barcode;
  502 if OpenFoodFacts is unreachable
- **Data change:** none — read-only preview
- **CLI trigger:** menu option **8 — Look up barcode**

### `GET /external/search?name=<name>`
- **Inputs:** query param `name` (required)
- **Output:** array of normalized products — 200; 400 missing name;
  502 if OpenFoodFacts is unreachable
- **Data change:** none
- **CLI trigger:** menu option **9 — Search by product name**

### `POST /items/import/<barcode>`
- **Inputs:** barcode in the path; optional JSON body with `price` and
  `quantity` (both default to 0 — OpenFoodFacts has no local pricing)
- **Output:** the created inventory item — 201; 404 unknown barcode;
  409 if the barcode is already in inventory (checked **before** any
  network call); 502 if OpenFoodFacts is unreachable
- **Data change:** **appends** the fetched-and-normalized product to the
  array with a new `id` and `source: "openfoodfacts"`
- **CLI trigger:** menu option **10 — Import into inventory** (prompts
  for selling price and initial stock)

## Design notes

- **Normalization boundary:** only `openfoodfacts.py` sees the raw
  external schema; routes and storage work exclusively with our item
  shape. Swapping the external provider would touch one file.
- **Why 409 on duplicate import:** re-importing a barcode would create a
  second row for the same physical product; the correct workflow is to
  PATCH the existing item's quantity instead. The CLI surfaces the
  existing item id in the error message.
- **Why prices are overrides on import:** OpenFoodFacts is a food *facts*
  database — it has no retail prices, so the employee supplies the local
  selling price (KES) at import time.
