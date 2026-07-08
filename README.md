# Inventory Management System — Flask REST API

Administrator portal backend for an e-commerce website. Employees can add,
edit, view, and delete inventory items, and pull real-time product data from
the [OpenFoodFacts API](https://world.openfoodfacts.org/) to supplement
product details.

> Full documentation (routes, CLI usage, architecture) lands with the
> `feature/docs` branch. This stub marks the project scaffold.

## Stack

- Python 3.12 · Flask 3.0 · Requests
- pipenv for dependency management (versions pinned)
- pytest test suite
- In-memory array as simulated data storage

## Quick start

```bash
pipenv install --dev
pipenv run python app.py        # API on http://127.0.0.1:5000
pipenv run python cli.py        # interactive CLI (separate terminal)
pipenv run pytest               # test suite
```
