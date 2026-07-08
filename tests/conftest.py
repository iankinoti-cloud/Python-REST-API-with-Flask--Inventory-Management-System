"""Shared pytest fixtures."""

import pytest

import storage
from app import create_app


@pytest.fixture()
def client():
    """Flask test client backed by a freshly-seeded inventory array."""
    storage.reset()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client
    storage.reset()
