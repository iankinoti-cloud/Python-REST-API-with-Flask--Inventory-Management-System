"""Thin client for the public OpenFoodFacts API.

Only this module talks to the network. It normalizes OpenFoodFacts'
sprawling product payloads down to the fields our inventory stores, so the
rest of the app never sees the raw external schema.
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT_SECONDS = 10
HEADERS = {"User-Agent": "InventoryManagementSystem/1.0 (student project)"}


class ExternalAPIError(Exception):
    """Raised when OpenFoodFacts is unreachable or answers with an error."""


def normalize_product(product):
    """Map a raw OpenFoodFacts product dict onto our inventory fields."""
    brands = (product.get("brands") or "").split(",")[0].strip()
    categories = (product.get("categories") or "").split(",")[0].strip()
    return {
        "barcode": product.get("code"),
        "name": product.get("product_name")
        or product.get("product_name_en")
        or "Unknown product",
        "brand": brands or None,
        "category": categories or "Uncategorized",
        "image_url": product.get("image_front_url") or product.get("image_url"),
        "nutriscore": product.get("nutriscore_grade"),
        "source": "openfoodfacts",
    }


def fetch_product(barcode):
    """Fetch one product by barcode. Returns a normalized dict, or None
    when OpenFoodFacts does not know the barcode."""
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise ExternalAPIError(f"OpenFoodFacts is unreachable: {exc}") from exc

    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise ExternalAPIError(
            f"OpenFoodFacts answered with HTTP {response.status_code}"
        )

    payload = response.json()
    if payload.get("status") != 1 or "product" not in payload:
        return None
    return normalize_product(payload["product"])


def search_products(name, limit=5):
    """Search products by name. Returns a list of normalized dicts."""
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
    }
    try:
        response = requests.get(
            f"{BASE_URL}/cgi/search.pl",
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ExternalAPIError(f"OpenFoodFacts is unreachable: {exc}") from exc

    if response.status_code != 200:
        raise ExternalAPIError(
            f"OpenFoodFacts answered with HTTP {response.status_code}"
        )

    products = response.json().get("products", [])
    return [normalize_product(p) for p in products if p.get("product_name")]
