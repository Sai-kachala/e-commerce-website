# E-commerce Product API

A small REST API for managing a product catalogue, built with FastAPI and SQLite. This project is intended to demonstrate API design, request validation, parameterized SQL, automated testing, containerization, and a CI workflow.

## Features

- Create, list, filter, paginate, retrieve, update, and delete products.
- Validate names, categories, prices, and stock values.
- Use parameterized SQL queries to avoid string-concatenated SQL.
- Store money as integer cents in SQLite to avoid floating-point storage errors.
- Provide interactive API documentation through OpenAPI/Swagger.
- Run automated API tests and build the project in Docker.

## Run locally

Python 3.11 or newer is recommended.

\`\`\`bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
\`\`\`

The API uses the local file data/shop.db by default. Set DATABASE_PATH to use another location.

Open http://127.0.0.1:8000/docs for interactive API documentation.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Basic liveness check |
| POST | /products | Create a product |
| GET | /products | List products; supports category, limit, and offset |
| GET | /products/{product_id} | Retrieve one product |
| PUT | /products/{product_id} | Replace a product |
| DELETE | /products/{product_id} | Delete a product |

Example request:

\`\`\`bash
curl -X POST http://127.0.0.1:8000/products \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Keyboard","category":"Electronics","price":"1499.00","stock":25}'
\`\`\`

## Run tests

\`\`\`bash
pip install -r requirements.txt
pytest -q
\`\`\`

Tests use temporary SQLite databases and do not modify your local development database.

## Run with Docker

\`\`\`bash
docker build -t ecommerce-product-api .
docker run --rm -p 8000:8000 -v ecommerce-data:/app/data ecommerce-product-api
\`\`\`

## Architecture

- FastAPI handles routing, request validation, and API documentation.
- Pydantic validates request payloads.
- SQLite stores products; values are passed with SQL parameters.
- Pytest and FastAPI TestClient cover API behavior.
- GitHub Actions runs tests on relevant pushes and pull requests.

## Current limitations and next milestones

This is a learning project, not a production commerce platform. It has no authentication or authorization, order/payment processing, inventory reservations, migrations, rate limiting, or managed database. Before production use, add authorization, structured logging, database migrations, stronger integration testing, secret management, and a managed database. A future learning milestone is to deploy it on AWS with infrastructure documented and costs constrained.
