from app.models.database import get_db


def find_admin_by_id(admin_id):
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash, created_at FROM admins WHERE id = ?",
        (admin_id,),
    ).fetchone()
    return dict(row) if row else None


def find_admin_by_username(username):
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash, created_at FROM admins WHERE username = ?",
        (username,),
    ).fetchone()
    return dict(row) if row else None


def create_admin(username, password_hash):
    db = get_db()
    db.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    db.commit()
