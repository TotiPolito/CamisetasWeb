from flask import Blueprint, abort, render_template

from app.models.product_model import fetch_all_products, fetch_media_by_token, fetch_product_by_slug
from app.services.media_service import stream_media


public_bp = Blueprint("public", __name__)

FILTER_ORDER = ["Todos", "Hombre", "Dama", "Niño", "Otros"]
SIZE_FILTER_ORDER = ["S", "M", "L", "XL", "XXL", "8", "10", "12", "14", "16"]


def _build_catalog_stats(products):
    return {
        "models": len(products),
        "units": sum(product["total_stock"] for product in products),
        "with_video": sum(1 for product in products if product["video_count"] > 0),
        "without_video": sum(1 for product in products if product["video_count"] == 0),
        "with_photo": sum(1 for product in products if product["image_count"] > 0),
        "without_photo": sum(1 for product in products if product["image_count"] == 0),
    }


def _build_filters(products):
    product_filters = {product["filter_group"] for product in products}
    return [filter_name for filter_name in FILTER_ORDER if filter_name == "Todos" or filter_name in product_filters]


def _build_size_filters(products):
    size_labels = {
        size["label"]
        for product in products
        for size in product["display_sizes"]
        if size["quantity"] > 0
    }
    ordered_sizes = [label for label in SIZE_FILTER_ORDER if label in size_labels]
    extra_sizes = sorted(size_labels.difference(ordered_sizes))
    return ["Todos"] + ordered_sizes + extra_sizes


@public_bp.get("/")
def home():
    products = fetch_all_products()
    filters = _build_filters(products)
    size_filters = _build_size_filters(products)
    stats = _build_catalog_stats(products)
    return render_template(
        "public/index.html",
        page_name="catalog",
        products=products,
        filters=filters,
        size_filters=size_filters,
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
