from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.models.product_model import fetch_all_products, fetch_product_by_id, update_product_stock
from app.services.auth_service import login_required, validate_csrf_token


admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin")
@login_required
def dashboard():
    products = fetch_all_products()
    return render_template("admin/dashboard.html", page_name="admin", products=products)


@admin_bp.post("/admin/product/<int:product_id>/stock")
@login_required
def update_stock(product_id):
    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    product = fetch_product_by_id(product_id)

    if not product:
        abort(404)

    updates = {}

    for size in product["display_sizes"]:
        field_name = f"size_{size['field_key']}"
        raw_value = request.form.get(field_name, str(size["quantity"])).strip()

        if not raw_value.isdigit():
            flash(f"El talle {size['label']} solo acepta numeros enteros positivos.", "error")
            return redirect(url_for("admin.dashboard") + f"#product-{product_id}")

        quantity = int(raw_value)
        updates[size["label"]] = {
            "quantity": quantity,
            "sort_order": size["sort_order"],
        }

    update_product_stock(product_id, updates)
    flash(f"Stock actualizado para {product['name']}.", "success")
    return redirect(url_for("admin.dashboard") + f"#product-{product_id}")
