"""FastAPI product catalogue backed by SQLite."""

from __future__ import annotations

import os
import sqlite3
from decimal import Decimal
from pathlib import Path as FilePath
from typing import Generator

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field


class ProductInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(ge=0)


def price_to_cents(price: Decimal) -> int:
    """Convert a validated two-decimal price to integer cents."""
    return int(price * 100)


def product_to_dict(row: sqlite3.Row) -> dict[str, object]:
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": f"{row['price_cents'] // 100}.{row['price_cents'] % 100:02d}",
        "stock": row["stock"],
        "created_at": row["created_at"],
    }


def create_app(database_path: str | None = None) -> FastAPI:
    db_path = database_path or os.getenv("DATABASE_PATH", "data/shop.db")
    if db_path != ":memory:":
        FilePath(db_path).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents > 0),
                stock INTEGER NOT NULL CHECK (stock >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

    app = FastAPI(
        title="E-commerce Product API",
        version="1.0.0",
        description="A learning API for a product catalogue.",
    )
    app.state.database_path = db_path

    def get_connection() -> Generator[sqlite3.Connection, None, None]:
        connection = sqlite3.connect(app.state.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @app.get("/health", tags=["operations"])
    def health_check() -> dict[str, str]:
        try:
            with sqlite3.connect(app.state.database_path) as connection:
                connection.execute("SELECT 1")
        except sqlite3.Error as exc:
            raise HTTPException(status_code=503, detail="Database unavailable") from exc
        return {"status": "ok"}

    @app.post("/products", status_code=status.HTTP_201_CREATED, tags=["products"])
    def create_product(
        product: ProductInput,
        connection: sqlite3.Connection = Depends(get_connection),
    ) -> dict[str, object]:
        cursor = connection.execute(
            """
            INSERT INTO products (name, category, price_cents, stock)
            VALUES (?, ?, ?, ?)
            """,
            (product.name.strip(), product.category.strip(), price_to_cents(product.price), product.stock),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        assert row is not None
        return product_to_dict(row)

    @app.get("/products", tags=["products"])
    def list_products(
        category: str | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        connection: sqlite3.Connection = Depends(get_connection),
    ) -> dict[str, object]:
        if category and category.strip():
            rows = connection.execute(
                """
                SELECT * FROM products
                WHERE lower(category) = lower(?)
                ORDER BY id LIMIT ? OFFSET ?
                """,
                (category.strip(), limit, offset),
            ).fetchall()
            count_row = connection.execute(
                "SELECT COUNT(*) AS total FROM products WHERE lower(category) = lower(?)",
                (category.strip(),),
            ).fetchone()
        else:
            rows = connection.execute(
                "SELECT * FROM products ORDER BY id LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            count_row = connection.execute(
                "SELECT COUNT(*) AS total FROM products"
            ).fetchone()
        return {"items": [product_to_dict(row) for row in rows], "total": count_row["total"]}

    @app.get("/products/{product_id}", tags=["products"])
    def get_product(
        product_id: int,
        connection: sqlite3.Connection = Depends(get_connection),
    ) -> dict[str, object]:
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product_to_dict(row)

    @app.put("/products/{product_id}", tags=["products"])
    def replace_product(
        product_id: int,
        product: ProductInput,
        connection: sqlite3.Connection = Depends(get_connection),
    ) -> dict[str, object]:
        cursor = connection.execute(
            """
            UPDATE products
            SET name = ?, category = ?, price_cents = ?, stock = ?
            WHERE id = ?
            """,
            (
                product.name.strip(),
                product.category.strip(),
                price_to_cents(product.price),
                product.stock,
                product_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        connection.commit()
        row = connection.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        assert row is not None
        return product_to_dict(row)

    @app.delete(
        "/products/{product_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["products"],
    )
    def delete_product(
        product_id: int,
        connection: sqlite3.Connection = Depends(get_connection),
    ) -> Response:
        cursor = connection.execute(
            "DELETE FROM products WHERE id = ?", (product_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        connection.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
