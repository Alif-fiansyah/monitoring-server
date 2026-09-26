import sqlite3
import hashlib
from datetime import datetime

DB_NAME = "monitor.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS monitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        status TEXT DEFAULT 'PENDING',
        last_latency_ms INTEGER DEFAULT 0,
        ssl_days_left INTEGER,
        server_header TEXT DEFAULT '-',
        content_type TEXT DEFAULT '-',
        response_size_kb REAL DEFAULT 0.0,
        last_checked_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    
    # Auto-migration kolom baru
    columns_to_add = [
        ("ssl_days_left", "INTEGER"),
        ("server_header", "TEXT DEFAULT '-'"),
        ("content_type", "TEXT DEFAULT '-'"),
        ("response_size_kb", "REAL DEFAULT 0.0")
    ]
    for col_name, col_type in columns_to_add:
        try:
            c.execute(f"ALTER TABLE monitors ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS ping_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_id INTEGER NOT NULL,
        status_code INTEGER,
        latency_ms INTEGER,
        is_up BOOLEAN NOT NULL,
        checked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (monitor_id) REFERENCES monitors(id) ON DELETE CASCADE
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        monitor_id INTEGER NOT NULL,
        error_message TEXT,
        started_at DATETIME NOT NULL,
        resolved_at DATETIME,
        duration_minutes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'OPEN',
        FOREIGN KEY (monitor_id) REFERENCES monitors(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def create_user(username, password):
    try:
        conn = get_connection()
        conn.cursor().execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.strip(), hash_password(password))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    conn = get_connection()
    row = conn.cursor().execute(
        "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
        (username.strip(), hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def add_monitor(user_id, name, url):
    conn = get_connection()
    conn.cursor().execute(
        "INSERT INTO monitors (user_id, name, url) VALUES (?, ?, ?)",
        (user_id, name.strip(), url.strip())
    )
    conn.commit()
    conn.close()

def get_user_monitors(user_id):
    conn = get_connection()
    rows = conn.cursor().execute(
        "SELECT * FROM monitors WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_monitor(monitor_id, user_id):
    conn = get_connection()
    conn.cursor().execute("DELETE FROM monitors WHERE id = ? AND user_id = ?", (monitor_id, user_id))
    conn.commit()
    conn.close()

def get_ping_logs(monitor_id, limit=35):
    conn = get_connection()
    rows = conn.cursor().execute(
        "SELECT * FROM ping_logs WHERE monitor_id = ? ORDER BY checked_at DESC LIMIT ?",
        (monitor_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def get_incidents(user_id):
    conn = get_connection()
    rows = conn.cursor().execute("""
        SELECT i.*, m.name as monitor_name, m.url 
        FROM incidents i 
        JOIN monitors m ON i.monitor_id = m.id 
        WHERE m.user_id = ? 
        ORDER BY i.started_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
