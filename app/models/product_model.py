import mimetypes
import re
import secrets
import unicodedata
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from app.models.database import get_db


CATEGORY_LABELS = {
    "Dama": "Dama",
    "Hombre": "Hombre",
    "Niños": "Niño",
    "Niño": "Niño",
    "Nino": "Niño",
    "Especial": "Otros",
    "Otros": "Otros",
}

SIZE_PROFILES = {
    "Dama": ["S", "M", "L", "XL", "XXL"],
    "Hombre": ["S", "M", "L", "XL", "XXL"],
    "Niños": ["8", "10", "12", "14", "16"],
    "Niño": ["8", "10", "12", "14", "16"],
    "Nino": ["8", "10", "12", "14", "16"],
    "Especial": ["S", "M", "L", "XL", "XXL"],
    "Otros": ["S", "M", "L", "XL", "XXL"],
}

DEFAULT_ACCENTS = {
    "Dama": "linear-gradient(135deg, #79a9dc, #c8def7)",
    "Hombre": "linear-gradient(135deg, #8da6de, #d9e2ff)",
    "Niños": "linear-gradient(135deg, #f6d364, #fff4b1)",
    "Niño": "linear-gradient(135deg, #f6d364, #fff4b1)",
    "Nino": "linear-gradient(135deg, #f6d364, #fff4b1)",
    "Especial": "linear-gradient(135deg, #7b2aa7, #ff39c6)",
    "Otros": "linear-gradient(135deg, #7b2aa7, #ff39c6)",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
HEX_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{6})")


def normalize_category_label(value):
    return CATEGORY_LABELS.get(value, value or "Otros")


def build_slug(value):
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    sanitized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return sanitized or secrets.token_hex(4)


def _clamp_color_channel(value):
    return max(0, min(255, int(round(value))))


def _lighten_hex_color(hex_color, ratio=0.42):
    color = str(hex_color or "").strip()
    if not HEX_COLOR_PATTERN.fullmatch(color):
        return "#d9e2ff"

    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)

    next_red = _clamp_color_channel(red + (255 - red) * ratio)
    next_green = _clamp_color_channel(green + (255 - green) * ratio)
    next_blue = _clamp_color_channel(blue + (255 - blue) * ratio)
    return f"#{next_red:02x}{next_green:02x}{next_blue:02x}"


def _extract_accent_color(accent_value, category_label):
    accent_text = str(accent_value or "").strip()
    match = HEX_COLOR_PATTERN.search(accent_text)
    if match:
        return match.group(0).lower()

    fallback_match = HEX_COLOR_PATTERN.search(DEFAULT_ACCENTS.get(category_label, DEFAULT_ACCENTS["Otros"]))
    if fallback_match:
        return fallback_match.group(0).lower()

    return "#8da6de"


def _build_accent_style(accent_value, category_label):
    accent_text = str(accent_value or "").strip()
    if HEX_COLOR_PATTERN.fullmatch(accent_text):
        accent_color = accent_text.lower()
        soft_color = _lighten_hex_color(accent_color)
        return f"linear-gradient(135deg, {accent_color}, {soft_color})"

    return accent_text or DEFAULT_ACCENTS.get(category_label, DEFAULT_ACCENTS["Otros"])


def _guess_mime_type(file_path, media_type):
    path = Path(file_path)
    if media_type == "video":
        if path.suffix.lower() in {".mov", ".mp4", ".m4v"}:
            return "video/mp4"
        if path.suffix.lower() == ".webm":
            return "video/webm"
        guessed, _encoding = mimetypes.guess_type(file_path)
        return guessed or "video/mp4"

    guessed, _encoding = mimetypes.guess_type(file_path)
    return guessed or "image/jpeg"


def _media_exists(file_path):
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    resolved_path = (media_root / Path(file_path)).resolve()

    if media_root not in resolved_path.parents and resolved_path != media_root:
        return False

    return resolved_path.exists() and resolved_path.is_file()


def _build_upload_relative_path(slug, filename):
    extension = Path(filename).suffix.lower()
    safe_name = secure_filename(Path(filename).stem) or "archivo"
    token = secrets.token_hex(4)
    return Path("uploads") / slug / f"{safe_name}-{token}{extension}"


def _is_managed_upload(file_path):
    path = Path(file_path)
    return path.parts[:1] == ("uploads",)


def _delete_media_file_if_managed(file_path):
    if not _is_managed_upload(file_path):
        return

    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    target_path = (media_root / Path(file_path)).resolve()

    if media_root not in target_path.parents:
        return

    if target_path.exists() and target_path.is_file():
        target_path.unlink()

    parent = target_path.parent
    while parent != media_root and parent.exists():
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


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


def _get_size_profile(product_row, sizes):
    profile = SIZE_PROFILES.get(product_row["category"], [])
    if profile:
        return profile

    return [size["label"] for size in sizes]


def _build_display_sizes(product_row, sizes):
    profile = _get_size_profile(product_row, sizes)
    size_lookup = {size["label"]: size for size in sizes}
    display_sizes = []

    for index, label in enumerate(profile):
        size = size_lookup.get(label)
        if size:
            display_sizes.append(
                {
                    **size,
                    "available": size["quantity"] > 0,
                    "missing": False,
                    "field_key": label,
                }
            )
            continue

        display_sizes.append(
            {
                "id": None,
                "label": label,
                "quantity": 0,
                "sort_order": index,
                "available": False,
                "missing": True,
                "field_key": label,
            }
        )

    for size in sizes:
        if size["label"] in profile:
            continue
        display_sizes.append(
            {
                **size,
                "available": size["quantity"] > 0,
                "missing": False,
                "field_key": size["label"],
            }
        )

    return display_sizes


def _serialize_product(row, sizes, media):
    images = [item for item in media if item["kind"] == "image"]
    videos = [item for item in media if item["kind"] == "video"]
    preview_media = images[0] if images else (videos[0] if videos else None)
    display_sizes = _build_display_sizes(row, sizes)
    available_sizes = [size["label"] for size in display_sizes if size["quantity"] > 0]
    category_label = normalize_category_label(row["category"])
    accent_color = _extract_accent_color(row["accent"], category_label)
    search_terms = " ".join(
        [
            row["name"],
            row["sku"] or "",
            row["family"],
            row["category"],
            category_label,
            row["description"],
            *[size["label"] for size in display_sizes],
        ]
    )

    return {
        "id": row["id"],
        "slug": row["slug"],
        "sku": row["sku"],
        "name": row["name"],
        "family": row["family"],
        "category": row["category"],
        "category_label": category_label,
        "filter_group": category_label,
        "accent": row["accent"],
        "accent_color": accent_color,
        "description": row["description"],
        "sizes": sizes,
        "display_sizes": display_sizes,
        "available_sizes": available_sizes,
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


def _next_product_sort_order(db):
    row = db.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_value FROM products").fetchone()
    return row["next_value"]


def _next_media_sort_order(db, product_id):
    row = db.execute(
        "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_value FROM product_media WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    return row["next_value"]


def fetch_all_products():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, slug, sku, name, family, category, accent, description, sort_order
        FROM products
        ORDER BY sort_order, id
        """
    ).fetchall()
    return [_hydrate_product(row) for row in rows]


def fetch_product_by_slug(slug):
    db = get_db()
    row = db.execute(
        """
        SELECT id, slug, sku, name, family, category, accent, description, sort_order
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
        SELECT id, slug, sku, name, family, category, accent, description, sort_order
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

    if not row or not _media_exists(row["file_path"]):
        return None

    return {
        "id": row["id"],
        "token": row["public_token"],
        "kind": row["media_type"],
        "label": row["label"],
        "file_path": row["file_path"],
        "mime_type": _guess_mime_type(row["file_path"], row["media_type"]),
    }


def fetch_product_media_by_id(media_id):
    db = get_db()
    row = db.execute(
        """
        SELECT id, product_id, public_token, media_type, label, file_path, sort_order
        FROM product_media
        WHERE id = ?
        """,
        (media_id,),
    ).fetchone()
    return dict(row) if row else None


def update_product_details_and_stock(product_id, product_payload, size_updates):
    db = get_db()
    db.execute("BEGIN")

    try:
        db.execute(
            """
            UPDATE products
            SET slug = ?, sku = ?, name = ?, family = ?, category = ?, accent = ?, description = ?
            WHERE id = ?
            """,
            (
                product_payload["slug"],
                product_payload["sku"],
                product_payload["name"],
                product_payload["family"],
                product_payload["category"],
                product_payload["accent"],
                product_payload["description"],
                product_id,
            ),
        )

        existing_sizes = {
            row["size_label"]: {"id": row["id"]}
            for row in db.execute(
                """
                SELECT id, size_label
                FROM product_sizes
                WHERE product_id = ?
                """,
                (product_id,),
            ).fetchall()
        }

        for label, payload in size_updates.items():
            quantity = payload["quantity"]
            sort_order = payload["sort_order"]
            existing = existing_sizes.get(label)

            if existing:
                db.execute(
                    "UPDATE product_sizes SET quantity = ?, sort_order = ? WHERE id = ?",
                    (quantity, sort_order, existing["id"]),
                )
                continue

            db.execute(
                """
                INSERT INTO product_sizes (product_id, size_label, quantity, sort_order)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, label, quantity, sort_order),
            )

        db.commit()
    except Exception:
        db.rollback()
        raise


def create_product(product_payload):
    db = get_db()
    sort_order = _next_product_sort_order(db)
    cursor = db.execute(
        """
        INSERT INTO products (slug, sku, name, family, category, accent, description, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_payload["slug"],
            product_payload["sku"],
            product_payload["name"],
            product_payload["family"],
            product_payload["category"],
            product_payload["accent"],
            product_payload["description"],
            sort_order,
        ),
    )
    product_id = cursor.lastrowid

    for size_order, label in enumerate(SIZE_PROFILES.get(product_payload["category"], []), start=1):
        db.execute(
            """
            INSERT INTO product_sizes (product_id, size_label, quantity, sort_order)
            VALUES (?, ?, 0, ?)
            """,
            (product_id, label, size_order),
        )

    db.commit()
    return product_id


def create_product_media(product_id, product_slug, uploads):
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    db = get_db()
    next_order = _next_media_sort_order(db, product_id)
    saved_total = 0

    for upload in uploads:
        filename = secure_filename(upload.filename or "")
        if not filename:
            continue

        extension = Path(filename).suffix.lower()
        if extension in IMAGE_EXTENSIONS:
            media_type = "image"
        elif extension in VIDEO_EXTENSIONS:
            media_type = "video"
        else:
            continue

        relative_path = _build_upload_relative_path(product_slug, filename)
        target_path = (media_root / relative_path).resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        upload.save(target_path)

        db.execute(
            """
            INSERT INTO product_media (product_id, public_token, media_type, label, file_path, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                secrets.token_urlsafe(18),
                media_type,
                Path(filename).stem,
                relative_path.as_posix(),
                next_order,
            ),
        )
        next_order += 1
        saved_total += 1

    db.commit()
    return saved_total


def delete_product_media(media_id):
    db = get_db()
    media_row = fetch_product_media_by_id(media_id)
    if not media_row:
        return None

    db.execute("DELETE FROM product_media WHERE id = ?", (media_id,))
    db.commit()
    _delete_media_file_if_managed(media_row["file_path"])
    return media_row["product_id"]


def delete_product(product_id):
    db = get_db()
    product = fetch_product_by_id(product_id)
    if not product:
        return None

    media_paths = [item["file_path"] for item in product["media"]]
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()

    for file_path in media_paths:
        _delete_media_file_if_managed(file_path)

    return product


def build_product_payload(name, category, sku="", slug="", family="", description="", accent=""):
    normalized_category = normalize_category_label(category)
    resolved_name = str(name or "").strip()
    resolved_slug = build_slug(slug or resolved_name)
    resolved_family = str(family or normalized_category).strip() or normalized_category
    resolved_sku = str(sku or "").strip() or None
    resolved_description = str(description or "").strip()
    resolved_accent = _build_accent_style(accent, normalized_category)

    return {
        "slug": resolved_slug,
        "sku": resolved_sku,
        "name": resolved_name,
        "family": resolved_family,
        "category": normalized_category,
        "accent": resolved_accent,
        "description": resolved_description,
    }
