# Demo Cheat-Sheet

Keep this open in a terminal while you demo:

    less CHEATSHEET.md        (q to quit)

Everything here is written so you can read it out loud while you work.

---

## 1. The barcodes (copy-paste from here)

Already in the inventory (seeded — options 1, 2, 8 work on these):

| Barcode         | Product                        |
|-----------------|--------------------------------|
| 3017620422003   | Nutella (Ferrero)              |
| 5449000000996   | Coca-Cola                      |
| 8076809513388   | Pesto alla Genovese (Barilla)  |
| 5000159407236   | Snickers (Mars)                |
| 3175680011480   | Biscuits Sésame (Gerblé)       |
| 3228857000852   | Pain 100% Mie (Harrys)         |
| 6161100000017   | Exe Wheat Flour 2kg (local)    |
| 6161100000024   | Kilimanjaro Water 1L (local)   |

NOT in the inventory yet (use these for option 10 — import; all
verified live on OpenFoodFacts):

| Barcode         | Product                        |
|-----------------|--------------------------------|
| 8000500310427   | Nutella Biscuits (Ferrero)     |
| 7613034626844   | Chocapic cereal (Nestlé)       |
| 5000112637922   | Coca-Cola (different pack)     |

Fails on purpose (good for showing error handling):

| Input           | What you get                        |
|-----------------|-------------------------------------|
| 0000000000000   | 404 — OpenFoodFacts doesn't know it |
| 3017620422003 on option 10 | 409 — already in inventory (it's seeded Nutella) |

---

## 2. Starting up

Terminal 1 — the API (the "shop's back office"):

    pipenv run python app.py

Say: "This starts the Flask server. It holds our inventory in memory —
think of it as the shopkeeper who actually touches the shelves."

Terminal 2 — the CLI (the "front desk"):

    pipenv run python cli.py

Say: "The CLI never touches the data itself. It just sends HTTP requests
to the API — the same way a website's admin panel would. That's why the
menu shows the route next to each option."

---

## 3. The demo, step by step

**Option 1 — View all items.**
Say: "GET /items returns the whole array. Eight seeded products, each
with an ID — that ID is how every other route finds an item."

**Option 2 — View item by ID.** Type `1`.
Say: "GET /items/1 — one item, straight from the array. Try 999 to show
the 404: the API answers with a clean JSON error, not a crash."

**Option 5 — Add item manually.** Any product you like.
Say: "POST /items appends to the array and hands back the new item with
its auto-assigned ID — max existing ID plus one."

**Option 6 — Edit item.** Use the ID you just created; change only price.
Say: "PATCH means partial update — I leave every other field blank and
they keep their values. Only what I typed changes."

**Option 8 — Look up barcode.** Paste `3017620422003`.
Say: "Now we leave our building. The API calls OpenFoodFacts live, gets a
huge messy payload, and normalizes it down to just the fields our
inventory understands. This is a preview — nothing is saved yet."

**Option 10 — Import into inventory.** Paste `8000500310427`, price 350,
stock 20.
Say: "Same fetch, but this time the product is appended to our array with
my local price — OpenFoodFacts knows food facts, not Kenyan prices, so
the employee supplies those. Run option 1 again: it's on the shelf now."

**Option 10 again — same barcode.**
Say: "409 Conflict — the API refuses a duplicate barcode and tells me
which item ID already has it. The right move is to PATCH that item's
quantity instead of creating a twin."

**Option 7 — Delete item.** Delete the one you imported; confirm with `y`.
Say: "DELETE removes it from the array — and the CLI asks first, because
there's no undo in a demo."

**Option 4 — Low-stock report.**
Say: "A helper route: everything at or below the threshold. Kilimanjaro
Water is seeded with quantity 3, so it always shows up — that's the
restocking to-do list."

---

## 4. If something goes wrong

- CLI says "Cannot reach the API" → Terminal 1 isn't running. Start it.
- Option 8/9/10 says 502 → no internet or OpenFoodFacts is down. The
  local options (1-7) still work; that's the point of the error handler.
- Want a clean slate? Restart the API — the array re-seeds itself.
