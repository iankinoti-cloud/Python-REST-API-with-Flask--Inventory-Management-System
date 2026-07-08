"""Tests for the simulated data storage (the mock database array)."""

import pytest

import storage


@pytest.fixture(autouse=True)
def fresh_inventory():
    storage.reset()
    yield
    storage.reset()


class TestSeedData:
    def test_seed_has_eight_items_with_unique_ids(self):
        items = storage.all_items()
        assert len(items) == 8
        assert sorted(item["id"] for item in items) == [1, 2, 3, 4, 5, 6, 7, 8]

    @pytest.mark.parametrize(
        "required_field", ["id", "barcode", "name", "price", "quantity", "source"]
    )
    def test_every_seed_item_has_required_field(self, required_field):
        assert all(required_field in item for item in storage.all_items())


class TestRead:
    def test_get_item_returns_matching_item(self):
        assert storage.get_item(1)["name"] == "Nutella"

    @pytest.mark.parametrize("missing_id", [0, 9, -1, 999])
    def test_get_item_returns_none_beyond_boundaries(self, missing_id):
        assert storage.get_item(missing_id) is None

    def test_all_items_filters_by_category_case_insensitively(self):
        names = {item["name"] for item in storage.all_items(category="beverages")}
        assert names == {"Coca-Cola", "Kilimanjaro Drinking Water 1L"}


class TestCreate:
    def test_create_appends_and_assigns_next_id(self):
        created = storage.create_item({"name": "Blue Band 500g", "price": 260, "quantity": 12})
        assert created["id"] == 9
        assert storage.get_item(9)["name"] == "Blue Band 500g"
        assert len(storage.all_items()) == 9

    def test_create_defaults_source_to_manual(self):
        created = storage.create_item({"name": "Mandazi Mix"})
        assert created["source"] == "manual"

    def test_ids_are_not_reused_after_delete(self):
        storage.delete_item(8)
        created = storage.create_item({"name": "Ugali Flour"})
        assert created["id"] == 8  # max remaining id is 7, so next is 8
        storage.delete_item(8)
        assert storage.create_item({"name": "Sukari 1kg"})["id"] == 8


class TestUpdate:
    def test_update_applies_partial_changes_in_place(self):
        updated = storage.update_item(2, {"price": 90.0, "quantity": 100})
        assert (updated["price"], updated["quantity"]) == (90.0, 100)
        assert updated["name"] == "Coca-Cola"  # untouched fields survive

    def test_update_ignores_id_and_unknown_fields(self):
        updated = storage.update_item(2, {"id": 999, "hacker_field": "x"})
        assert updated["id"] == 2
        assert "hacker_field" not in updated

    def test_update_missing_item_returns_none(self):
        assert storage.update_item(999, {"price": 1}) is None


class TestDelete:
    def test_delete_removes_item_and_returns_true(self):
        assert storage.delete_item(3) is True
        assert storage.get_item(3) is None
        assert len(storage.all_items()) == 7

    def test_delete_missing_item_returns_false(self):
        assert storage.delete_item(999) is False
        assert len(storage.all_items()) == 8


class TestHelpers:
    @pytest.mark.parametrize(
        "query,expected_names",
        [
            ("nutella", ["Nutella"]),
            ("coca", ["Coca-Cola"]),
            ("5449000000996", ["Coca-Cola"]),  # barcode search
            ("zzz-no-match", []),
        ],
    )
    def test_search_matches_name_brand_or_barcode(self, query, expected_names):
        assert [item["name"] for item in storage.search_items(query)] == expected_names

    def test_low_stock_includes_items_at_threshold_boundary(self):
        storage.update_item(1, {"quantity": 5})  # exactly at threshold
        names = {item["name"] for item in storage.low_stock(threshold=5)}
        assert names == {"Nutella", "Kilimanjaro Drinking Water 1L"}
