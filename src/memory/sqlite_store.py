import sqlite3
import datetime
from src.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cleanup_old_memory(days_to_keep: int = 14):
    """Deletes records older than N days to keep the database lightweight and fast."""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_to_keep)).isoformat()
    cursor.execute('DELETE FROM seen_news WHERE seen_at < ?', (cutoff_date,))
    conn.commit()
    conn.close()

def init_db():
    """Initializes the table and triggers auto-cleanup."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_news (
            id_hash TEXT PRIMARY KEY,
            title TEXT,
            domain TEXT,
            seen_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    
    # AUTO-CLEANUP: Runs automatically every time J.A.R.V.I.S. starts
    cleanup_old_memory()

def is_already_seen(id_hash: str) -> bool:
    """Checks if a news item (identified by unique hash) has already been processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM seen_news WHERE id_hash = ?', (id_hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_seen_article(id_hash: str, title: str, domain: str):
    """Saves a news item in the database as 'seen'."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        cursor.execute(
            'INSERT INTO seen_news (id_hash, title, domain, seen_at) VALUES (?, ?, ?, ?)',
            (id_hash, title, domain, now)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already present
    finally:
        conn.close()

# Initialize DB and clean memory on the first import of this module
init_db()