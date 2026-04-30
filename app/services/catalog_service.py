import json
import secrets

from flask import current_app

from app.models.database import get_db
from app.services.auth_service import ensure_default_admin


def seed_catalog_if_empty():
    db = get_db()
    product_count = db.execute("SELECT COUNT(*) AS total FROM products").fetchone()["total"]

    if product_count > 0:
        ensure_default_admin()
        return

    with current_app.config["PRODUCT_SEED_PATH"].open("r", encoding="utf-8") as seed_file:
        payload = json.load(seed_file)

    for product_order, product in enumerate(payload["products"], start=1):
        cursor = db.execute(
            """
            INSERT INTO products (slug, name, family, category, accent, description, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["slug"],
                product["name"],
                product["family"],
                product["category"],
                product["accent"],
                product["description"],
                product_order,
            ),
        )
        product_id = cursor.lastrowid

        for size_order, size in enumerate(product["sizes"], start=1):
            db.execute(
                """
                INSERT INTO product_sizes (product_id, size_label, quantity, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, size["label"], size["quantity"], size_order),
            )

        for media_order, media in enumerate(product["media"], start=1):
            db.execute(
                """
                INSERT INTO product_media (product_id, public_token, media_type, label, file_path, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    secrets.token_urlsafe(18),
                    media["type"],
                    media["label"],
                    media["path"],
                    media_order,
                ),
            )

    db.commit()
    ensure_default_admin()
