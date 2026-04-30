from flask import Blueprint, abort, render_template

from app.models.product_model import fetch_all_products, fetch_media_by_token, fetch_product_by_slug
from app.services.media_service import stream_media


public_bp = Blueprint("public", __name__)


def _build_catalog_stats(products):
    return {
        "models": len(products),
        "units": sum(product["total_stock"] for product in products),
        "with_video": sum(1 for product in products if product["video_count"] > 0),
        "without_photo": sum(1 for product in products if product["image_count"] == 0),
    }


def _build_filters(products):
    ordered_categories = []

    for product in products:
        category = product["category"]
        if category not in ordered_categories:
            ordered_categories.append(category)

    return ["Todos", *ordered_categories]


@public_bp.get("/")
def home():
    products = fetch_all_products()
    filters = _build_filters(products)
    stats = _build_catalog_stats(products)
    return render_template(
        "public/index.html",
        page_name="catalog",
        products=products,
        filters=filters,
        stats=stats,
    )


@public_bp.get("/camiseta/<slug>")
def product_detail(slug):
    product = fetch_product_by_slug(slug)

    if not product:
        abort(404)

    return render_template(
        "public/product_detail.html",
        page_name="product",
        product=product,
    )


@public_bp.get("/media/<token>")
def media(token):
    media_record = fetch_media_by_token(token)

    if not media_record:
        abort(404)

    return stream_media(media_record)
