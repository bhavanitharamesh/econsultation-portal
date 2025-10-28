import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

conn = sqlite3.connect('econsult.db', check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password_hash TEXT,
mobile TEXT,
created_at TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS comments (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
sector TEXT,
comment TEXT,
sentiment TEXT,
summary TEXT,
passcode TEXT UNIQUE,
status TEXT,
created_at TEXT
)""")
conn.commit()

def create_user(u, p, m):
    try:
        h = generate_password_hash(p)
        cur.execute("INSERT INTO users (username, password_hash, mobile, created_at) VALUES (?,?,?,?)",
                    (u, h, m, datetime.now()))
        conn.commit()
        return True, "User registered successfully"
    except Exception as e:
        return False, str(e)

def authenticate_user(u, p):
    cur.execute("SELECT id, password_hash FROM users WHERE username=?", (u,))
    row = cur.fetchone()
    if not row: return False, "User not found"
    uid, ph = row
    if check_password_hash(ph, p): return True, uid
    return False, "Incorrect password"

def add_comment(uid, sector, text, sentiment, summary):
    code = str(uuid.uuid4())[:8]
    cur.execute("INSERT INTO comments (user_id, sector, comment, sentiment, summary, passcode, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (uid, sector, text, sentiment, summary, code, "Submitted", datetime.now()))
    conn.commit()
    return code

def get_comment_by_passcode(code):
    cur.execute("SELECT sector, comment, sentiment, summary, status FROM comments WHERE passcode=?", (code,))
    row = cur.fetchone()
    if not row: return None
    keys = ["sector", "comment", "sentiment", "summary", "status"]
    return dict(zip(keys, row))

def list_comments_for_user(uid):
    cur.execute("SELECT sector, comment, sentiment, passcode FROM comments WHERE user_id=? ORDER BY id DESC", (uid,))
    rows = cur.fetchall()
    cols = ["sector", "comment", "sentiment", "passcode"]
    return [dict(zip(cols, r)) for r in rows]
