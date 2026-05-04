from pathlib import Path

from flask import abort, current_app, request, send_file

try:
    from PIL import Image, ImageOps
except Exception:  # pragma: no cover - fallback when Pillow is unavailable
    Image = None
    ImageOps = None


IMAGE_VARIANTS = {
    "card": {"max_width": 900, "quality": 82},
    "detail": {"max_width": 1500, "quality": 84},
    "gallery": {"max_width": 1400, "quality": 82},
    "admin": {"max_width": 720, "quality": 78},
}


def _resolve_media_path(relative_path):
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    requested_path = (media_root / Path(relative_path)).resolve()

    if media_root not in requested_path.parents and requested_path != media_root:
        abort(404)

    if not requested_path.exists() or not requested_path.is_file():
        abort(404)

    return requested_path


def _build_cache_path(source_path, variant_name):
    cache_root = Path(current_app.config["MEDIA_CACHE_ROOT"]).resolve()
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    relative_source = source_path.relative_to(media_root)
    source_stamp = str(int(source_path.stat().st_mtime))
    return cache_root / relative_source.parent / f"{relative_source.stem}-{variant_name}-{source_stamp}.webp"


def _serve_optimized_image(source_path, variant_name):
    if Image is None or variant_name not in IMAGE_VARIANTS:
        return None

    cache_path = _build_cache_path(source_path, variant_name)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    if not cache_path.exists():
        settings = IMAGE_VARIANTS[variant_name]
        with Image.open(source_path) as image:
            processed = ImageOps.exif_transpose(image)
            if processed.mode not in {"RGB", "RGBA"}:
                processed = processed.convert("RGB")

            processed.thumbnail((settings["max_width"], settings["max_width"] * 2))
            processed.save(
                cache_path,
                format="WEBP",
                quality=settings["quality"],
                method=6,
                optimize=True,
            )

    response = send_file(cache_path, mimetype="image/webp", as_attachment=False, conditional=True, max_age=86400)
    response.headers["Content-Disposition"] = "inline"
    response.headers["Cache-Control"] = "private, max-age=86400"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex, noarchive"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


def stream_media(media_record):
    requested_path = _resolve_media_path(media_record["file_path"])
    variant_name = request.args.get("variant", "").strip().lower()

    if media_record["kind"] == "image":
        optimized_response = _serve_optimized_image(requested_path, variant_name)
        if optimized_response is not None:
            return optimized_response

    response = send_file(
        requested_path,
        mimetype=media_record["mime_type"],
        as_attachment=False,
        conditional=True,
        max_age=0,
    )
    response.headers["Content-Disposition"] = "inline"
    response.headers["Cache-Control"] = "private, no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Robots-Tag"] = "noindex, noarchive"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    return response
