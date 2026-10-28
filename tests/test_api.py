"""API tests using isolated temporary SQLite databases."""

from fastapi.testclient import TestClient

from main import create_app


def make_client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    return TestClient(app)


def test_health_check(tmp_path):
    with make_client(tmp_path) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_read_product(tmp_path):
    with make_client(tmp_path) as client:
        created = client.post(
            "/products",
            json={
                "name": "Keyboard",
                "category": "Electronics",
                "price": "1499.00",
                "stock": 20,
            },
        )
        assert created.status_code == 201
        product = created.json()
        assert product["price"] == "1499.00"
        assert product["stock"] == 20

        fetched = client.get(f"/products/{product['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["name"] == "Keyboard"


def test_invalid_product_is_rejected(tmp_path):
    with make_client(tmp_path) as client:
        response = client.post(
            "/products",
            json={
                "name": "X",
                "category": "Electronics",
                "price": "-1.00",
                "stock": -2,
            },
        )
    assert response.status_code == 422


def test_filter_pagination_and_update(tmp_path):
    with make_client(tmp_path) as client:
        first = client.post(
            "/products",
            json={"name": "Keyboard", "category": "Electronics", "price": "10.00", "stock": 5},
        ).json()
        client.post(
            "/products",
            json={"name": "Notebook", "category": "Stationery", "price": "2.50", "stock": 100},
        )

        filtered = client.get("/products", params={"category": "electronics", "limit": 1})
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1
        assert len(filtered.json()["items"]) == 1

        updated = client.put(
            f"/products/{first['id']}",
            json={"name": "Mechanical Keyboard", "category": "Electronics", "price": "15.00", "stock": 3},
        )
        assert updated.status_code == 200
        assert updated.json()["price"] == "15.00"
        assert updated.json()["stock"] == 3


def test_delete_and_not_found(tmp_path):
    with make_client(tmp_path) as client:
        product = client.post(
            "/products",
            json={"name": "Mouse", "category": "Electronics", "price": "5.00", "stock": 4},
        ).json()

        deleted = client.delete(f"/products/{product['id']}")
        assert deleted.status_code == 204
        missing = client.get(f"/products/{product['id']}")
        assert missing.status_code == 404
