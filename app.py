"""Flask REST API for the e-commerce inventory administrator portal.

CRUD routes operate on the simulated data storage in ``storage.py``.
External OpenFoodFacts routes are added by the external-api feature.
"""

from flask import Flask, jsonify, request

import openfoodfacts
import storage


def create_app():
    app = Flask(__name__)

    # ------------------------------------------------------------------ meta

    @app.get("/")
    def index():
        return {
            "service": "Inventory Management API",
            "status": "ok",
            "items_in_stock": len(storage.all_items()),
        }

    @app.errorhandler(404)
    def not_found(_error):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(400)
    def bad_request(error):
        return {"error": error.description or "Bad request"}, 400

    # ------------------------------------------------------------------ CRUD

    @app.get("/items")
    def list_items():
        category = request.args.get("category")
        return jsonify(storage.all_items(category=category))

    @app.get("/items/<int:item_id>")
    def get_item(item_id):
        item = storage.get_item(item_id)
        if item is None:
            return {"error": f"Item {item_id} not found"}, 404
        return item

    @app.post("/items")
    def create_item():
        data = request.get_json(silent=True)
        if not data or not data.get("name"):
            return {"error": "JSON body with a 'name' field is required"}, 400
        try:
            item = storage.create_item(data)
        except (TypeError, ValueError):
            return {"error": "'price' and 'quantity' must be numeric"}, 400
        return item, 201

    @app.patch("/items/<int:item_id>")
    def update_item(item_id):
        data = request.get_json(silent=True)
        if not data:
            return {"error": "JSON body with fields to update is required"}, 400
        item = storage.update_item(item_id, data)
        if item is None:
            return {"error": f"Item {item_id} not found"}, 404
        return item

    @app.delete("/items/<int:item_id>")
    def delete_item(item_id):
        if not storage.delete_item(item_id):
            return {"error": f"Item {item_id} not found"}, 404
        return {"deleted": item_id}

    # --------------------------------------------------------------- helpers

    @app.get("/items/search")
    def search_items():
        query = request.args.get("q", "").strip()
        if not query:
            return {"error": "Query parameter 'q' is required"}, 400
        return jsonify(storage.search_items(query))

    @app.get("/items/low-stock")
    def low_stock():
        try:
            threshold = int(request.args.get("threshold", 5))
        except ValueError:
            return {"error": "'threshold' must be an integer"}, 400
        return jsonify(storage.low_stock(threshold=threshold))

    # ---------------------------------------------------- external API (OFF)

    @app.errorhandler(openfoodfacts.ExternalAPIError)
    def external_api_down(error):
        return {"error": str(error)}, 502

    @app.get("/external/products/<barcode>")
    def external_product(barcode):
        product = openfoodfacts.fetch_product(barcode)
        if product is None:
            return {"error": f"Barcode {barcode} not found on OpenFoodFacts"}, 404
        return product

    @app.get("/external/search")
    def external_search():
        name = request.args.get("name", "").strip()
        if not name:
            return {"error": "Query parameter 'name' is required"}, 400
        return jsonify(openfoodfacts.search_products(name))

    @app.post("/items/import/<barcode>")
    def import_item(barcode):
        """Fetch a product from OpenFoodFacts and add it to the inventory
        array. Optional JSON body supplies price/quantity overrides."""
        existing = [i for i in storage.all_items() if i["barcode"] == barcode]
        if existing:
            return {
                "error": f"Barcode {barcode} is already in inventory "
                f"(item id {existing[0]['id']})"
            }, 409

        product = openfoodfacts.fetch_product(barcode)
        if product is None:
            return {"error": f"Barcode {barcode} not found on OpenFoodFacts"}, 404

        overrides = request.get_json(silent=True) or {}
        product["price"] = overrides.get("price", 0)
        product["quantity"] = overrides.get("quantity", 0)
        item = storage.create_item(product)
        return item, 201

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
