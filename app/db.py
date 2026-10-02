from pathlib import Path
import sqlite3

from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(_error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = Path(__file__).with_name('schema.sql')
    db.executescript(schema_path.read_text(encoding='utf-8'))
    # Backward-compatible migration for databases created before Hackathon Utilities.
    columns = {row['name'] for row in db.execute('PRAGMA table_info(users)').fetchall()}
    if 'is_hackathon' not in columns:
        db.execute('ALTER TABLE users ADD COLUMN is_hackathon INTEGER NOT NULL DEFAULT 0 CHECK (is_hackathon IN (0, 1))')
    need_columns = {row['name'] for row in db.execute('PRAGMA table_info(needs)').fetchall()}
    if 'price' not in need_columns:
        # Existing needs are legacy records; give them a small visible default
        # rather than breaking the database migration. New needs must provide
        # a positive price through the API.
        db.execute('ALTER TABLE needs ADD COLUMN price REAL NOT NULL DEFAULT 1 CHECK (price > 0)')
    need_columns = {row['name'] for row in db.execute('PRAGMA table_info(needs)').fetchall()}
    if 'start_time' not in need_columns:
        db.execute("ALTER TABLE needs ADD COLUMN start_time TEXT NOT NULL DEFAULT '09:00 AM'")
    if 'end_time' not in need_columns:
        db.execute("ALTER TABLE needs ADD COLUMN end_time TEXT NOT NULL DEFAULT '05:00 PM'")
    db.execute('CREATE INDEX IF NOT EXISTS idx_users_hackathon ON users(is_hackathon, created_at)')
    db.commit()
