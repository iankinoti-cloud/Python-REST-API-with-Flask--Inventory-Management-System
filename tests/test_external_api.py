"""Tests for the OpenFoodFacts client and the external routes.

Only the HTTP boundary (``requests.get``) is mocked — everything else runs
for real, including normalization and the Flask routes.
"""

from unittest.mock import Mock, patch

import pytest
import requests

import openfoodfacts

RAW_NUTELLA = {
    "code": "3017620422003",
    "product_name": "Nutella",
    "brands": "Ferrero, Nutella",
    "categories": "Spreads, Sweet spreads",
    "image_front_url": "https://images.openfoodfacts.org/nutella.jpg",
    "nutriscore_grade": "e",
}


def ok_response(payload):
    response = Mock(status_code=200)
    response.json.return_value = payload
    return response


class TestNormalizeProduct:
    def test_maps_raw_payload_to_inventory_fields(self):
        assert openfoodfacts.normalize_product(RAW_NUTELLA) == {
            "barcode": "3017620422003",
            "name": "Nutella",
            "brand": "Ferrero",
            "category": "Spreads",
            "image_url": "https://images.openfoodfacts.org/nutella.jpg",
            "nutriscore": "e",
            "source": "openfoodfacts",
        }

    def test_missing_fields_get_safe_defaults(self):
        normalized = openfoodfacts.normalize_product({"code": "123"})
        assert normalized["name"] == "Unknown product"
        assert normalized["brand"] is None
        assert normalized["category"] == "Uncategorized"


class TestFetchProduct:
    @patch("openfoodfacts.requests.get")
    def test_returns_normalized_product_on_status_1(self, mock_get):
        mock_get.return_value = ok_response(
            {"status": 1, "product": RAW_NUTELLA}
        )
        product = openfoodfacts.fetch_product("3017620422003")
        assert product["name"] == "Nutella"
        assert product["source"] == "openfoodfacts"
        requested_url = mock_get.call_args.args[0]
        assert requested_url.endswith("/api/v2/product/3017620422003.json")

    @pytest.mark.parametrize(
        "response",
        [
            Mock(status_code=404),
            ok_response({"status": 0}),
            ok_response({"status": 1}),  # status 1 but no product payload
        ],
        ids=["http-404", "status-0", "no-product-key"],
    )
    @patch("openfoodfacts.requests.get")
    def test_unknown_barcode_returns_none(self, mock_get, response):
        mock_get.return_value = response
        assert openfoodfacts.fetch_product("0000000000000") is None

    @patch("openfoodfacts.requests.get", side_effect=requests.ConnectionError("boom"))
    def test_network_failure_raises_external_api_error(self, _mock_get):
        with pytest.raises(openfoodfacts.ExternalAPIError):
            openfoodfacts.fetch_product("3017620422003")

    @patch("openfoodfacts.requests.get")
    def test_server_error_raises_external_api_error(self, mock_get):
        mock_get.return_value = Mock(status_code=500)
        with pytest.raises(openfoodfacts.ExternalAPIError):
            openfoodfacts.fetch_product("3017620422003")


class TestSearchProducts:
    @patch("openfoodfacts.requests.get")
    def test_returns_normalized_list_skipping_nameless_products(self, mock_get):
        mock_get.return_value = ok_response(
            {"products": [RAW_NUTELLA, {"code": "999"}]}  # second has no name
        )
        results = openfoodfacts.search_products("nutella")
        assert [p["name"] for p in results] == ["Nutella"]


class TestExternalRoutes:
    @patch("openfoodfacts.requests.get")
    def test_external_product_route_returns_normalized_json(self, mock_get, client):
        mock_get.return_value = ok_response({"status": 1, "product": RAW_NUTELLA})
        response = client.get("/external/products/3017620422003")
        assert response.status_code == 200
        assert response.get_json()["brand"] == "Ferrero"

    @patch("openfoodfacts.requests.get")
    def test_external_product_route_404_for_unknown_barcode(self, mock_get, client):
        mock_get.return_value = ok_response({"status": 0})
        assert client.get("/external/products/0000000000000").status_code == 404

    @patch("openfoodfacts.requests.get", side_effect=requests.ConnectionError("boom"))
    def test_external_routes_return_502_when_api_is_down(self, _mock_get, client):
        assert client.get("/external/products/3017620422003").status_code == 502

    def test_external_search_requires_name_param(self, client):
        assert client.get("/external/search").status_code == 400

    @patch("openfoodfacts.requests.get")
    def test_external_search_route_returns_results(self, mock_get, client):
        mock_get.return_value = ok_response({"products": [RAW_NUTELLA]})
        body = client.get("/external/search?name=nutella").get_json()
        assert [p["name"] for p in body] == ["Nutella"]


class TestImportRoute:
    RAW_KITKAT = {
        "code": "7613034626844",
        "product_name": "KitKat",
        "brands": "Nestlé",
        "categories": "Snacks",
        "nutriscore_grade": "d",
    }

    @patch("openfoodfacts.requests.get")
    def test_import_fetches_and_appends_to_inventory(self, mock_get, client):
        mock_get.return_value = ok_response(
            {"status": 1, "product": self.RAW_KITKAT}
        )
        response = client.post(
            "/items/import/7613034626844", json={"price": 120, "quantity": 30}
        )
        assert response.status_code == 201
        body = response.get_json()
        assert (body["id"], body["name"], body["price"], body["quantity"]) == (
            9,
            "KitKat",
            120.0,
            30,
        )
        # behavioral check: importable through the normal CRUD read
        assert client.get("/items/9").get_json()["source"] == "openfoodfacts"

    @patch("openfoodfacts.requests.get")
    def test_import_defaults_price_and_quantity_to_zero(self, mock_get, client):
        mock_get.return_value = ok_response(
            {"status": 1, "product": self.RAW_KITKAT}
        )
        body = client.post("/items/import/7613034626844").get_json()
        assert (body["price"], body["quantity"]) == (0.0, 0)

    def test_import_duplicate_barcode_returns_409_without_network_call(self, client):
        with patch("openfoodfacts.requests.get") as mock_get:
            response = client.post("/items/import/3017620422003")  # seeded Nutella
        assert response.status_code == 409
        mock_get.assert_not_called()

    @patch("openfoodfacts.requests.get")
    def test_import_unknown_barcode_returns_404(self, mock_get, client):
        mock_get.return_value = ok_response({"status": 0})
        assert client.post("/items/import/0000000000000").status_code == 404
