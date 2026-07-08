"""Tests for the Flask CRUD and helper routes, via the real test client."""

import pytest

import storage


class TestIndex:
    def test_index_reports_status_and_stock_count(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.get_json() == {
            "service": "Inventory Management API",
            "status": "ok",
            "items_in_stock": 8,
        }


class TestListItems:
    def test_returns_all_seed_items(self, client):
        response = client.get("/items")
        assert response.status_code == 200
        assert len(response.get_json()) == 8

    def test_category_filter_is_case_insensitive(self, client):
        body = client.get("/items?category=BEVERAGES").get_json()
        assert {item["name"] for item in body} == {
            "Coca-Cola",
            "Kilimanjaro Drinking Water 1L",
        }


class TestGetItem:
    def test_returns_single_item_by_id(self, client):
        body = client.get("/items/1").get_json()
        assert (body["id"], body["name"], body["barcode"]) == (
            1,
            "Nutella",
            "3017620422003",
        )

    @pytest.mark.parametrize("missing_id", [0, 9, 999])
    def test_missing_ids_return_404_json_error(self, client, missing_id):
        response = client.get(f"/items/{missing_id}")
        assert response.status_code == 404
        assert "error" in response.get_json()


class TestCreateItem:
    def test_post_creates_item_and_returns_201(self, client):
        response = client.post(
            "/items",
            json={"name": "Blue Band 500g", "brand": "Upfield",
                  "category": "Spreads", "price": 260, "quantity": 12},
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body["id"] == 9
        assert body["source"] == "manual"
        # behavioral check: the item is now retrievable through the API
        assert client.get("/items/9").get_json()["name"] == "Blue Band 500g"

    @pytest.mark.parametrize(
        "payload",
        [None, {}, {"brand": "no-name-given"}],
        ids=["no-body", "empty-body", "missing-name"],
    )
    def test_invalid_payloads_return_400(self, client, payload):
        response = client.post("/items", json=payload)
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_non_numeric_price_returns_400(self, client):
        response = client.post(
            "/items", json={"name": "Bad Item", "price": "not-a-price"}
        )
        assert response.status_code == 400


class TestUpdateItem:
    def test_patch_applies_partial_update(self, client):
        response = client.patch("/items/2", json={"price": 90.0, "quantity": 95})
        assert response.status_code == 200
        body = response.get_json()
        assert (body["price"], body["quantity"], body["name"]) == (
            90.0,
            95,
            "Coca-Cola",
        )

    def test_patch_missing_item_returns_404(self, client):
        assert client.patch("/items/999", json={"price": 1}).status_code == 404

    def test_patch_without_body_returns_400(self, client):
        assert client.patch("/items/2").status_code == 400


class TestDeleteItem:
    def test_delete_removes_item(self, client):
        response = client.delete("/items/4")
        assert response.status_code == 200
        assert response.get_json() == {"deleted": 4}
        assert client.get("/items/4").status_code == 404

    def test_delete_missing_item_returns_404(self, client):
        assert client.delete("/items/999").status_code == 404


class TestHelperRoutes:
    @pytest.mark.parametrize(
        "query,expected_names",
        [
            ("nutella", ["Nutella"]),
            ("5449000000996", ["Coca-Cola"]),
            ("zzz-no-match", []),
        ],
    )
    def test_search_matches_by_name_or_barcode(self, client, query, expected_names):
        body = client.get(f"/items/search?q={query}").get_json()
        assert [item["name"] for item in body] == expected_names

    def test_search_without_query_returns_400(self, client):
        assert client.get("/items/search").status_code == 400

    def test_low_stock_respects_threshold_boundary(self, client):
        storage.update_item(1, {"quantity": 5})
        body = client.get("/items/low-stock?threshold=5").get_json()
        assert {item["name"] for item in body} == {
            "Nutella",
            "Kilimanjaro Drinking Water 1L",
        }

    def test_low_stock_with_non_integer_threshold_returns_400(self, client):
        assert client.get("/items/low-stock?threshold=abc").status_code == 400
