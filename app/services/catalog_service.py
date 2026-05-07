import json
import secrets

from flask import current_app

from app.models.database import get_db
from app.services.auth_service import ensure_default_admin


SKU_PREFIXES = {
    "Dama": "DAM",
    "Hombre": "HOM",
    "Niños": "NIN",
    "Niño": "NIN",
    "Especial": "ESP",
    "Otros": "ESP",
}


def _load_seed_payload():
    with current_app.config["PRODUCT_SEED_PATH"].open("r", encoding="utf-8") as seed_file:
        return json.load(seed_file)


def _build_fallback_sku(product, order):
    prefix = SKU_PREFIXES.get(product.get("category"), "CAT")
    return f"{prefix}-{order:03d}"


def _resolve_product_sku(product, order):
    return product.get("sku") or _build_fallback_sku(product, order)


def _ensure_catalog_skus(payload):
    db = get_db()
    products = payload["products"]
    sku_by_slug = {
        product["slug"]: _resolve_product_sku(product, order)
        for order, product in enumerate(products, start=1)
    }
    fallback_orders = {
        product["slug"]: order
        for order, product in enumerate(products, start=1)
    }

    rows = db.execute(
        """
        SELECT id, slug, category, sku
        FROM products
        ORDER BY sort_order, id
        """
    ).fetchall()

    has_changes = False

    for order, row in enumerate(rows, start=1):
        sku = sku_by_slug.get(row["slug"])
        if not sku:
            sku = _build_fallback_sku(
                {"category": row["category"]},
                fallback_orders.get(row["slug"], order),
            )

        current_sku = str(row["sku"] or "").strip()
        normalized_current = current_sku.removeprefix("TOT-")
        if normalized_current == sku:
            continue

        db.execute("UPDATE products SET sku = ? WHERE id = ?", (sku, row["id"]))
        has_changes = True

    if has_changes:
        db.commit()


def _ensure_catalog_prices(payload):
    db = get_db()
    price_by_slug = {
        product["slug"]: int(product.get("price_ars") or 0)
        for product in payload["products"]
    }
    rows = db.execute(
        """
        SELECT id, slug, price_ars
        FROM products
        ORDER BY sort_order, id
        """
    ).fetchall()

    has_changes = False

    for row in rows:
        desired_price = price_by_slug.get(row["slug"])
        if desired_price is None:
            continue
        if int(row["price_ars"] or 0) > 0:
            continue

        db.execute(
            "UPDATE products SET price_ars = ? WHERE id = ?",
            (desired_price, row["id"]),
        )
        has_changes = True

    if has_changes:
        db.commit()


def _insert_seed_product(db, product, product_order):
    cursor = db.execute(
        """
        INSERT INTO products (slug, sku, name, family, category, price_ars, accent, description, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product["slug"],
            _resolve_product_sku(product, product_order),
            product["name"],
            product["family"],
            product["category"],
            int(product.get("price_ars") or 0),
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


def _ensure_seed_products_exist(payload):
    db = get_db()
    existing_slugs = {
        row["slug"]
        for row in db.execute("SELECT slug FROM products").fetchall()
    }
    has_changes = False

    for product_order, product in enumerate(payload["products"], start=1):
        if product["slug"] in existing_slugs:
            continue
        _insert_seed_product(db, product, product_order)
        has_changes = True

    if has_changes:
        db.commit()


def seed_catalog_if_empty():
    db = get_db()
    product_count = db.execute("SELECT COUNT(*) AS total FROM products").fetchone()["total"]
    payload = _load_seed_payload()

    if product_count > 0:
        _ensure_seed_products_exist(payload)
        _ensure_catalog_skus(payload)
        _ensure_catalog_prices(payload)
        ensure_default_admin()
        return

    for product_order, product in enumerate(payload["products"], start=1):
        _insert_seed_product(db, product, product_order)

    db.commit()
    ensure_default_admin()
