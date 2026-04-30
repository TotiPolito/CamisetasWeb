from pathlib import Path

from flask import abort, current_app, send_file


def stream_media(media_record):
    media_root = Path(current_app.config["MEDIA_ROOT"]).resolve()
    requested_path = (media_root / Path(media_record["file_path"])).resolve()

    if media_root not in requested_path.parents and requested_path != media_root:
        abort(404)

    if not requested_path.exists() or not requested_path.is_file():
        abort(404)

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
