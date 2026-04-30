import mimetypes
from pathlib import Path

from flask import current_app

from app.models.database import get_db


def _guess_mime_type(file_path, media_type):
    guessed, _encoding = mimetypes.guess_type(file_path)
    if guessed:
        return guessed
    if media_type == "video":
        return "video/quicktime"
    return "image/jpeg"


def _fetch_sizes(db, product_id):
    rows = db.execute(
        """
        SELECT id, size_label, quantity, sort_order
        FROM product_sizes
        WHERE product_id = ?
        ORDER BY sort_order, id
        """,
        (product_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "label": row["size_label"],
            "quantity": row["quantity"],
            "sort_order": row["sort_order"],
        }
        for row in rows
    ]


def _media_exists(file_path):
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    resolved_path = (media_root / Path(file_path)).resolve()

    if media_root not in resolved_path.parents and resolved_path != media_root:
        return False

    return resolved_path.exists() and resolved_path.is_file()


def _fetch_media(db, product_id):
    rows = db.execute(
        """
        SELECT id, public_token, media_type, label, file_path, sort_order
        FROM product_media
        WHERE product_id = ?
        ORDER BY sort_order, id
        """,
        (product_id,),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "token": row["public_token"],
            "kind": row["media_type"],
            "label": row["label"],
            "file_path": row["file_path"],
            "mime_type": _guess_mime_type(row["file_path"], row["media_type"]),
            "sort_order": row["sort_order"],
        }
        for row in rows
        if _media_exists(row["file_path"])
    ]


def _serialize_product(row, sizes, media):
    images = [item for item in media if item["kind"] == "image"]
    videos = [item for item in media if item["kind"] == "video"]
    preview_media = images[0] if images else (videos[0] if videos else None)
    search_terms = " ".join(
        [
            row["name"],
            row["family"],
            row["category"],
            row["description"],
            *[size["label"] for size in sizes],
        ]
    )

    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "family": row["family"],
        "category": row["category"],
        "accent": row["accent"],
        "description": row["description"],
        "sizes": sizes,
        "media": media,
        "images": images,
        "videos": videos,
        "preview_media": preview_media,
        "image_count": len(images),
        "video_count": len(videos),
        "total_stock": sum(size["quantity"] for size in sizes),
        "search_blob": search_terms,
    }


def _hydrate_product(row):
    db = get_db()
    sizes = _fetch_sizes(db, row["id"])
    media = _fetch_media(db, row["id"])
    return _serialize_product(row, sizes, media)


def fetch_all_products():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, slug, name, family, category, accent, description, sort_order
        FROM products
        ORDER BY sort_order, id
        """
    ).fetchall()
    return [_hydrate_product(row) for row in rows]


def fetch_product_by_slug(slug):
    db = get_db()
    row = db.execute(
        """
        SELECT id, slug, name, family, category, accent, description, sort_order
        FROM products
        WHERE slug = ?
        """,
        (slug,),
    ).fetchone()
    return _hydrate_product(row) if row else None


def fetch_product_by_id(product_id):
    db = get_db()
    row = db.execute(
        """
        SELECT id, slug, name, family, category, accent, description, sort_order
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    ).fetchone()
    return _hydrate_product(row) if row else None


def fetch_media_by_token(token):
    db = get_db()
    row = db.execute(
        """
        SELECT id, public_token, media_type, label, file_path
        FROM product_media
        WHERE public_token = ?
        """,
        (token,),
    ).fetchone()

    if not row:
        return None

    if not _media_exists(row["file_path"]):
        return None

    return {
        "id": row["id"],
        "token": row["public_token"],
        "kind": row["media_type"],
        "label": row["label"],
        "file_path": row["file_path"],
        "mime_type": _guess_mime_type(row["file_path"], row["media_type"]),
    }


def update_product_stock(product_id, size_updates):
    db = get_db()
    db.execute("BEGIN")

    try:
        valid_size_ids = {
            row["id"]
            for row in db.execute(
                "SELECT id FROM product_sizes WHERE product_id = ?",
                (product_id,),
            ).fetchall()
        }

        for size_id, quantity in size_updates.items():
            if size_id not in valid_size_ids:
                continue
            db.execute(
                "UPDATE product_sizes SET quantity = ? WHERE id = ?",
                (quantity, size_id),
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
