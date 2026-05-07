import sqlite3

from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    sku TEXT UNIQUE,
    name TEXT NOT NULL,
    family TEXT NOT NULL,
    category TEXT NOT NULL,
    price_ars INTEGER NOT NULL DEFAULT 0,
    accent TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_sizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    size_label TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    UNIQUE(product_id, size_label)
);

CREATE TABLE IF NOT EXISTS product_media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    public_token TEXT NOT NULL UNIQUE,
    media_type TEXT NOT NULL,
    label TEXT NOT NULL,
    file_path TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);
"""


def get_db():
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE_PATH"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def initialize_database(app):
    database_path = app.config["DATABASE_PATH"]
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA)
        existing_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        if "sku" not in existing_columns:
            connection.execute("ALTER TABLE products ADD COLUMN sku TEXT")
        if "price_ars" not in existing_columns:
            connection.execute("ALTER TABLE products ADD COLUMN price_ars INTEGER NOT NULL DEFAULT 0")
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku
            ON products(sku)
            WHERE sku IS NOT NULL
            """
        )

    app.teardown_appcontext(close_db)
