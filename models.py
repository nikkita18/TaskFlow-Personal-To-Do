import hmac
import hashlib
import os
import secrets
import time
from datetime import datetime, timezone
import config
from database import get_db

# Password Hashing Utilities using PBKDF2 with SHA-256 and 100,000 rounds
def hash_password(password: str) -> str:
    """Generate salted PBKDF2-HMAC-SHA256 password hash."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    """Safely verify a password against stored PBKDF2 hash using constant-time comparison."""
    try:
        method, salt, key_hex = stored_hash.split("$")
        parts = method.split(":")
        iterations = int(parts[2])
        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(computed.hex(), key_hex)
    except Exception:
        return False

def get_current_iso_time() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# User Operations
def create_user(email: str, password: str, name: str = ""):
    db = get_db()
    email_clean = email.strip().lower()
    pw_hash = hash_password(password)
    created_at = get_current_iso_time()
    
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
        (email_clean, pw_hash, (name or "").strip(), created_at)
    )
    db.commit()
    user_id = cursor.lastrowid
    return {
        "id": user_id,
        "email": email_clean,
        "name": (name or "").strip(),
        "created_at": created_at
    }

def get_user_by_email(email: str):
    db = get_db()
    email_clean = email.strip().lower()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
    return cur.fetchone()

def get_user_by_id(user_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cur.fetchone()

def update_user_password(user_id: int, new_password: str):
    db = get_db()
    pw_hash = hash_password(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pw_hash, user_id))
    db.commit()

# Session / Token Operations
def create_session(user_id: int) -> tuple[str, int]:
    db = get_db()
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    expires_at = now + config.TOKEN_EXPIRY_SECONDS
    db.execute(
        "INSERT INTO active_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at)
    )
    db.commit()
    return token, config.TOKEN_EXPIRY_SECONDS

def get_user_from_token(token: str):
    db = get_db()
    now = int(time.time())
    cur = db.cursor()
    cur.execute("""
        SELECT u.id, u.email, u.name, u.created_at
        FROM active_tokens t
        JOIN users u ON t.user_id = u.id
        WHERE t.token = ? AND t.expires_at > ?
    """, (token, now))
    row = cur.fetchone()
    if row:
        return dict(row)
    return None

def delete_session(token: str) -> bool:
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM active_tokens WHERE token = ?", (token,))
    db.commit()
    return cur.rowcount > 0

# Rate Limiting Operations (Brute-force protection)
def record_login_attempt(identifier: str):
    db = get_db()
    now = int(time.time())
    db.execute("INSERT INTO login_attempts (identifier, attempt_time) VALUES (?, ?)", (identifier, now))
    db.commit()

def is_login_rate_limited(identifier: str) -> bool:
    db = get_db()
    now = int(time.time())
    cutoff = now - config.LOGIN_LOCKOUT_SECONDS
    # Clean up older records periodically
    db.execute("DELETE FROM login_attempts WHERE attempt_time < ?", (cutoff,))
    db.commit()
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM login_attempts WHERE identifier = ? AND attempt_time >= ?", (identifier, cutoff))
    row = cur.fetchone()
    return (row["cnt"] if row else 0) >= config.LOGIN_MAX_FAILED_ATTEMPTS

def clear_login_attempts(identifier: str):
    db = get_db()
    db.execute("DELETE FROM login_attempts WHERE identifier = ?", (identifier,))
    db.commit()

# Task Operations
def serialize_task(row) -> dict:
    """Format database row to the exact JSON contract."""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"] or "",
        "dueDate": row["due_date"],
        "priority": row["priority"],
        "done": bool(row["done"]),
        "createdAt": row["created_at"]
    }

def create_task(user_id: int, title: str, description: str = "", due_date: str = None, priority: str = "medium") -> dict:
    db = get_db()
    created_at = get_current_iso_time()
    cur = db.cursor()
    cur.execute("""
        INSERT INTO tasks (user_id, title, description, due_date, priority, done, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (user_id, title.strip(), (description or "").strip(), due_date, priority.lower(), created_at))
    db.commit()
    task_id = cur.lastrowid
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return serialize_task(cur.fetchone())

def get_tasks(user_id: int, status: str = "all", priority: str = None, q: str = None, sort: str = "createdAt", order: str = "desc") -> list[dict]:
    db = get_db()
    query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [user_id]

    # Filter: status
    if status == "open":
        query += " AND done = 0"
    elif status == "done":
        query += " AND done = 1"

    # Filter: priority
    if priority:
        query += " AND priority = ?"
        params.append(priority.lower())

    # Filter: search query q (case-insensitive substring in title or description)
    if q:
        query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ?)"
        like_term = f"%{q.lower()}%"
        params.extend([like_term, like_term])

    # Sorting
    order_dir = "ASC" if order.lower() == "asc" else "DESC"

    if sort == "dueDate":
        # When sorting ascending, null due dates come LAST
        if order_dir == "ASC":
            query += " ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC, id ASC"
        else:
            query += " ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date DESC, id DESC"
    elif sort == "priority":
        # low < medium < high
        if order_dir == "ASC":
            query += " ORDER BY CASE priority WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 ELSE 2 END ASC, id ASC"
        else:
            query += " ORDER BY CASE priority WHEN 'low' THEN 1 WHEN 'medium' THEN 2 WHEN 'high' THEN 3 ELSE 2 END DESC, id DESC"
    else:
        # Default: createdAt
        query += f" ORDER BY created_at {order_dir}, id {order_dir}"

    cur = db.cursor()
    cur.execute(query, params)
    return [serialize_task(row) for row in cur.fetchall()]

def get_task(user_id: int, task_id: int):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    row = cur.fetchone()
    if row:
        return serialize_task(row)
    return None

def update_task(user_id: int, task_id: int, updates: dict):
    db = get_db()
    # Check ownership
    cur = db.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    if not cur.fetchone():
        return None

    fields = []
    values = []

    if "title" in updates:
        fields.append("title = ?")
        values.append(updates["title"].strip())
    if "description" in updates:
        fields.append("description = ?")
        values.append((updates["description"] or "").strip())
    if "dueDate" in updates:
        fields.append("due_date = ?")
        values.append(updates["dueDate"])
    if "priority" in updates:
        fields.append("priority = ?")
        values.append(updates["priority"].lower())
    if "done" in updates:
        fields.append("done = ?")
        values.append(1 if updates["done"] else 0)

    if not fields:
        return None

    values.extend([task_id, user_id])
    sql = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
    db.execute(sql, values)
    db.commit()

    return get_task(user_id, task_id)

def delete_task(user_id: int, task_id: int) -> bool:
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
    db.commit()
    return cur.rowcount > 0
