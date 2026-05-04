import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models.product_model import (
    SIZE_PROFILES,
    build_product_payload,
    create_product,
    create_product_media,
    delete_product,
    delete_product_media,
    fetch_all_products,
    fetch_product_by_id,
    normalize_category_label,
    update_product_details_and_stock,
)
from app.services.auth_service import login_required, validate_csrf_token


admin_bp = Blueprint("admin", __name__)


def _build_size_updates(product, category_value):
    normalized_category = normalize_category_label(category_value)
    current_sizes = {size["label"]: size for size in product["display_sizes"]}
    profile = SIZE_PROFILES.get(normalized_category, [])

    labels = []
    for label in profile:
        if label not in labels:
            labels.append(label)
    for size in product["display_sizes"]:
        if size["label"] not in labels:
            labels.append(size["label"])

    updates = {}
    for index, label in enumerate(labels, start=1):
        current_size = current_sizes.get(label, {"quantity": 0})
        field_name = f"size_{label}"
        raw_value = request.form.get(field_name, str(current_size["quantity"])).strip()

        if not raw_value.isdigit():
            raise ValueError(f"El talle {label} solo acepta numeros enteros positivos.")

        updates[label] = {
            "quantity": int(raw_value),
            "sort_order": index,
        }

    return updates


def _redirect_to_product(product_id):
    return redirect(url_for("admin.dashboard") + f"#product-{product_id}")


@admin_bp.get("/admin")
@login_required
def dashboard():
    products = fetch_all_products()
    return render_template("admin/dashboard.html", page_name="admin", products=products)


@admin_bp.post("/admin/product/create")
@login_required
def create_product_action():
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()

    if not name or not category:
        flash("Nombre y categoria son obligatorios para crear un modelo.", "error")
        return redirect(url_for("admin.dashboard") + "#new-product")

    payload = build_product_payload(
        name=name,
        category=category,
        sku=request.form.get("sku", ""),
        slug=request.form.get("slug", ""),
        family=request.form.get("family", ""),
        description=request.form.get("description", ""),
        accent=request.form.get("accent", ""),
    )

    try:
        product_id = create_product(payload)
    except sqlite3.IntegrityError:
        flash("No se pudo crear el modelo porque el slug o el SKU ya existen.", "error")
        return redirect(url_for("admin.dashboard") + "#new-product")

    flash(f"Modelo creado: {payload['name']}.", "success")
    return _redirect_to_product(product_id)


@admin_bp.post("/admin/product/<int:product_id>")
@login_required
def update_product(product_id):
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    product = fetch_product_by_id(product_id)
    if not product:
        abort(404)

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()

    if not name or not category:
        flash("Nombre y categoria son obligatorios.", "error")
        return _redirect_to_product(product_id)

    payload = build_product_payload(
        name=name,
        category=category,
        sku=request.form.get("sku", ""),
        slug=request.form.get("slug", ""),
        family=request.form.get("family", ""),
        description=request.form.get("description", ""),
        accent=request.form.get("accent", ""),
    )

    try:
        size_updates = _build_size_updates(product, payload["category"])
        update_product_details_and_stock(product_id, payload, size_updates)
    except ValueError as error:
        flash(str(error), "error")
        return _redirect_to_product(product_id)
    except sqlite3.IntegrityError:
        flash("No se pudo guardar porque el slug o el SKU ya estan en uso.", "error")
        return _redirect_to_product(product_id)

    flash(f"Producto actualizado: {payload['name']}.", "success")
    return _redirect_to_product(product_id)


@admin_bp.post("/admin/product/<int:product_id>/media")
@login_required
def upload_product_media(product_id):
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    product = fetch_product_by_id(product_id)
    if not product:
        abort(404)

    uploads = [file for file in request.files.getlist("media_files") if file and file.filename]
    if not uploads:
        flash("Selecciona al menos un archivo para subir.", "error")
        return _redirect_to_product(product_id)

    saved_total = create_product_media(product_id, product["slug"], uploads)
    if saved_total == 0:
        flash("No se subio ningun archivo valido. Usa imagenes o videos compatibles.", "error")
        return _redirect_to_product(product_id)

    flash(f"Se agregaron {saved_total} archivo(s) a {product['name']}.", "success")
    return _redirect_to_product(product_id)


@admin_bp.post("/admin/media/<int:media_id>/delete")
@login_required
def delete_product_media_action(media_id):
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    product_id = delete_product_media(media_id)
    if not product_id:
        abort(404)

    flash("Archivo eliminado del producto.", "success")
    return _redirect_to_product(product_id)


@admin_bp.post("/admin/product/<int:product_id>/delete")
@login_required
def delete_product_action(product_id):
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    deleted_product = delete_product(product_id)
    if not deleted_product:
        abort(404)

    flash(f"Se elimino el modelo {deleted_product['name']}.", "success")
    return redirect(url_for("admin.dashboard"))
