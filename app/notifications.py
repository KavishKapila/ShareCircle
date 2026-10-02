from .db import get_db

def create_notification(user_id, kind, body, link):
    db = get_db()
    db.execute(
        'INSERT INTO notifications (user_id, type, body, link) VALUES (?, ?, ?, ?)',
        (user_id, kind, body, link),
    )
    db.commit()

def unread_count(user_id):
    db = get_db()
    row = db.execute('SELECT COUNT(*) AS c FROM notifications WHERE user_id = ? AND read = 0', (user_id,)).fetchone()
    return int(row['c'])
