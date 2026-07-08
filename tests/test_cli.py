"""End-to-end tests for the CLI.

A real Flask server runs in a background thread and the CLI talks to it
over actual HTTP — nothing between the CLI and the storage array is mocked.
Only the OpenFoodFacts client functions are stubbed, since they are the
network boundary to the outside world.
"""

import threading
from unittest.mock import patch

import pytest
from werkzeug.serving import make_server

import cli
import openfoodfacts
import storage
from app import create_app

FAKE_KITKAT = {
    "barcode": "7613034626844",
    "name": "KitKat",
    "brand": "Nestlé",
    "category": "Snacks",
    "image_url": None,
    "nutriscore": "d",
    "source": "openfoodfacts",
}


@pytest.fixture()
def live_api(monkeypatch):
    """Serve the real app on a random local port and point the CLI at it."""
    storage.reset()
    server = make_server("127.0.0.1", 0, create_app())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(cli, "API_URL", f"http://127.0.0.1:{server.server_port}")
    yield
    server.shutdown()
    thread.join()
    storage.reset()


def feed_input(monkeypatch, *lines):
    answers = iter(lines)
    monkeypatch.setattr("builtins.input", lambda _="": next(answers))


class TestFormatting:
    def test_fmt_item_fixed_vector(self):
        line = cli.fmt_item(
            {"id": 7, "name": "Ugali Flour", "brand": "Jogoo",
             "price": 199.5, "quantity": 3, "source": "manual"}
        )
        assert line == (
            "[  7] Ugali Flour                         Jogoo           "
            "    KES 199.50  qty:    3  (manual)"
        )


class TestStartup:
    def test_check_api_reports_connection_and_stock(self, live_api, capsys):
        assert cli.check_api() is True
        assert "8 items in stock" in capsys.readouterr().out

    def test_check_api_fails_cleanly_when_api_is_down(self, monkeypatch, capsys):
        monkeypatch.setattr(cli, "API_URL", "http://127.0.0.1:1")
        assert cli.check_api() is False
        assert "Cannot reach the API" in capsys.readouterr().out


class TestInventoryActions:
    def test_view_all_lists_every_seed_item(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "")  # no category filter
        cli.view_all()
        out = capsys.readouterr().out
        assert "Nutella" in out
        assert "-- 8 item(s)" in out

    def test_view_one_unknown_id_prints_api_error(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "999")
        cli.view_one()
        assert "!! 404" in capsys.readouterr().out

    def test_add_item_creates_item_in_storage(self, live_api, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            "Blue Band 500g", "Upfield", "Spreads", "6001234567890", "260", "12",
        )
        cli.add_item()
        assert "Created:" in capsys.readouterr().out
        created = storage.get_item(9)
        assert (created["name"], created["price"], created["quantity"]) == (
            "Blue Band 500g", 260.0, 12,
        )

    def test_edit_item_patches_only_supplied_fields(self, live_api, monkeypatch, capsys):
        # id=2, keep name/brand/category, change price + quantity
        feed_input(monkeypatch, "2", "", "", "", "95", "80")
        cli.edit_item()
        assert "Updated:" in capsys.readouterr().out
        item = storage.get_item(2)
        assert (item["name"], item["price"], item["quantity"]) == (
            "Coca-Cola", 95.0, 80,
        )

    def test_delete_item_requires_confirmation(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "3", "n")
        cli.delete_item()
        assert "Cancelled." in capsys.readouterr().out
        assert storage.get_item(3) is not None

    def test_delete_item_removes_after_confirmation(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "3", "y")
        cli.delete_item()
        assert "Deleted item 3." in capsys.readouterr().out
        assert storage.get_item(3) is None

    def test_low_stock_report_uses_default_threshold(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "")
        cli.low_stock_report()
        out = capsys.readouterr().out
        assert "Kilimanjaro Drinking Water 1L" in out
        assert "-- 1 item(s)" in out


class TestExternalActions:
    def test_lookup_barcode_prints_normalized_product(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "7613034626844")
        with patch.object(openfoodfacts, "fetch_product", return_value=FAKE_KITKAT):
            cli.lookup_barcode()
        out = capsys.readouterr().out
        assert "KitKat" in out
        assert "Nestlé" in out

    def test_search_external_lists_results(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "kitkat")
        with patch.object(openfoodfacts, "search_products", return_value=[FAKE_KITKAT]):
            cli.search_external()
        assert "7613034626844" in capsys.readouterr().out

    def test_import_barcode_adds_product_to_inventory(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "7613034626844", "120", "30")
        with patch.object(openfoodfacts, "fetch_product", return_value=dict(FAKE_KITKAT)):
            cli.import_barcode()
        assert "Imported into inventory:" in capsys.readouterr().out
        imported = storage.get_item(9)
        assert (imported["name"], imported["source"], imported["quantity"]) == (
            "KitKat", "openfoodfacts", 30,
        )


class TestMenuLoop:
    def test_run_rejects_unknown_option_then_exits(self, live_api, monkeypatch, capsys):
        feed_input(monkeypatch, "42", "0")
        cli.run()
        out = capsys.readouterr().out
        assert "!! '42' is not a menu option." in out
        assert "Goodbye!" in out

    def test_run_aborts_when_api_is_unreachable(self, monkeypatch, capsys):
        monkeypatch.setattr(cli, "API_URL", "http://127.0.0.1:1")
        cli.run()  # must not reach the input() loop
        assert "Start it first" in capsys.readouterr().out
