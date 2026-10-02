"""Populate ShareCircle with realistic Dehradun-area demo data."""
from datetime import datetime, timedelta
import random

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db

SEED_PASSWORD = 'password123'
random.seed(2026)

PEOPLE = [
    ('Asha Verma', 'asha', 'asha@example.local'),
    ('Kabir Mehta', 'kabir', 'kabir@example.local'),
    ('Meera Joshi', 'meera', 'meera@example.local'),
    ('Rohan Rawat', 'rohan', 'rohan@example.local'),
    ('Ishita Negi', 'ishita', 'ishita@example.local'),
    ('Arjun Bisht', 'arjun', 'arjun@example.local'),
    ('Naina Kapoor', 'naina', 'naina@example.local'),
    ('Dev Thakur', 'dev', 'dev@example.local'),
    ('Pooja Shah', 'pooja', 'pooja@example.local'),
    ('Aditya Rana', 'aditya', 'aditya@example.local'),
    ('Simran Kaur', 'simran', 'simran@example.local'),
    ('Yash Negi', 'yash', 'yash@example.local'),
    ('Riya Agarwal', 'riya', 'riya@example.local'),
    ('Manav Saini', 'manav', 'manav@example.local'),
    ('Tanya Bhandari', 'tanya', 'tanya@example.local'),
    ('Vivek Nautiyal', 'vivek', 'vivek@example.local'),
    ('Ananya Dutta', 'ananya', 'ananya@example.local'),
    ('Harsh Pandey', 'harsh', 'harsh@example.local'),
    ('Sana Khan', 'sana', 'sana@example.local'),
    ('Kunal Chamoli', 'kunal', 'kunal@example.local'),
]
LOCATIONS = ['Rajpur Road', 'Clock Tower', 'Ballupur', 'Patel Nagar', 'Dalanwala', 'Clement Town', 'Vasant Vihar', 'Prem Nagar', 'Jakhan', 'Sahastradhara Road']
NEED_TEMPLATES = [
    ('Algebra tutor for class 9', 'Need weekend help with algebra and linear equations for a student preparing for school exams.', 'Education', 'medium'),
    ('Medicine pickup for neighbor', 'Looking for a reliable person who can pick up prescribed medicine from a nearby pharmacy this evening.', 'Health', 'high'),
    ('Winter clothes for two children', 'Seeking gently used jackets and sweaters for two school-age children before the colder weeks.', 'Clothing', 'medium'),
    ('Ride to hospital appointment', 'Need a safe ride to the hospital for an elderly family member on Tuesday morning.', 'Transport', 'high'),
    ('Resume review before interview', 'Would appreciate a mentor who can review a student resume and run through common interview questions.', 'Mentorship', 'low'),
    ('Groceries for senior citizen', 'Need help collecting a few grocery essentials and dropping them at a nearby home.', 'Elderly Care', 'medium'),
    ('Extra lunch boxes for event', 'Our community study group needs simple vegetarian lunch portions for a Saturday session.', 'Food', 'low'),
    ('Blood donor awareness volunteer', 'Need a volunteer to help share a local donation drive notice with nearby residents.', 'Health', 'medium'),
]
OFFER_TEMPLATES = [
    ('Weekend algebra tutoring', 'I can tutor algebra, equations, and exam practice for school students on Saturday and Sunday.', 'Education', 'Sat/Sun, 10am–1pm'),
    ('Can pick up medicines', 'Happy to pick up packed prescriptions from pharmacies around Rajpur Road and deliver them locally.', 'Health', 'Weekdays after 5pm'),
    ('Children clothing bundle', 'I have clean jackets, sweaters, and warm clothes suitable for school-age children.', 'Clothing', 'Flexible this week'),
    ('Morning hospital rides', 'I can help with short local rides to hospitals and clinics, especially early mornings.', 'Transport', 'Tue/Thu mornings'),
    ('Student resume mentoring', 'Can help students polish resumes, practice interviews, and plan first internship applications.', 'Mentorship', 'Saturday afternoons'),
    ('Senior grocery runs', 'I can pick up groceries and essentials for elderly neighbors within a short local radius.', 'Elderly Care', 'Most evenings'),
    ('Community meal portions', 'I can prepare simple vegetarian meal boxes for small community events with notice.', 'Food', 'Saturday mornings'),
    ('Share health drive info', 'Happy to help distribute verified health and donation-drive information in neighborhood groups.', 'Health', 'Evenings'),
]


def coord(i):
    return round(30.3165 + random.uniform(-0.05, 0.05), 6), round(78.0322 + random.uniform(-0.05, 0.05), 6)


def main():
    app = create_app()
    with app.app_context():
        db = get_db()
        user_ids = {}
        for index, (full_name, username, email) in enumerate(PEOPLE):
            row = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if row:
                user_ids[username] = row['id']
                continue
            created = (datetime.now() - timedelta(days=30 - min(index, 29))).strftime('%Y-%m-%d %H:%M:%S')
            db.execute('''
                INSERT INTO users (full_name, username, email, location, password_hash, messages_seen_at, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (full_name, username, email, LOCATIONS[index % len(LOCATIONS)] + ', Dehradun', generate_password_hash(SEED_PASSWORD), created))
            user_ids[username] = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']
        db.commit()

        if db.execute('SELECT COUNT(*) FROM needs').fetchone()[0] < 30:
            existing = db.execute('SELECT COUNT(*) FROM needs').fetchone()[0]
            for i in range(existing, 30):
                title, description, category, urgency = NEED_TEMPLATES[i % len(NEED_TEMPLATES)]
                owner = PEOPLE[i % len(PEOPLE)]
                lat, lng = coord(i + 40)
                created = (datetime.now() - timedelta(days=29 - i, hours=i % 8)).strftime('%Y-%m-%d %H:%M:%S')
                suffix = f' — request {i + 1}' if i >= len(NEED_TEMPLATES) else ''
                db.execute('''
                    INSERT INTO needs (user_id, title, description, category, urgency, status, lat, lng, created_at)
                    VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
                ''', (user_ids[owner[1]], title + suffix, description, category, urgency, lat, lng, created))
        if db.execute('SELECT COUNT(*) FROM offers').fetchone()[0] < 40:
            existing = db.execute('SELECT COUNT(*) FROM offers').fetchone()[0]
            for i in range(existing, 40):
                title, description, category, availability = OFFER_TEMPLATES[i % len(OFFER_TEMPLATES)]
                owner = PEOPLE[(i * 3 + 2) % len(PEOPLE)]
                lat, lng = coord(i + 80)
                created = (datetime.now() - timedelta(days=29 - (i * 29 // 39), minutes=i % 60)).strftime('%Y-%m-%d %H:%M:%S')
                suffix = f' — offer {i + 1}' if i >= len(OFFER_TEMPLATES) else ''
                db.execute('''
                    INSERT INTO offers (user_id, title, description, category, availability, status, lat, lng, created_at)
                    VALUES (?, ?, ?, ?, ?, 'available', ?, ?, ?)
                ''', (user_ids[owner[1]], title + suffix, description, category, availability, lat, lng, created))
        db.commit()

        completed = db.execute("SELECT COUNT(*) FROM matches WHERE status = 'completed'").fetchone()[0]
        if completed < 15:
            needs = db.execute("SELECT id, user_id FROM needs WHERE status = 'open' ORDER BY id LIMIT 15").fetchall()
            offers = db.execute("SELECT id, user_id FROM offers WHERE status = 'available' ORDER BY id LIMIT 15").fetchall()
            for i, (need, offer) in enumerate(zip(needs, offers)):
                created_at = datetime.now() - timedelta(days=14 - i)
                arrived_at = created_at + timedelta(hours=2)
                paid_at = arrived_at + timedelta(hours=3)
                completed_at = paid_at + timedelta(minutes=20)
                amount = 100 + (i * 35)
                db.execute('''
                    INSERT OR IGNORE INTO matches
                    (need_id, offer_id, status, otp, otp_attempts, amount_paid, arrived_at, paid_at, created_at, completed_at)
                    VALUES (?, ?, 'completed', '123456', 0, ?, ?, ?, ?, ?)
                ''', (need['id'], offer['id'], amount, arrived_at.strftime('%Y-%m-%d %H:%M:%S'), paid_at.strftime('%Y-%m-%d %H:%M:%S'), created_at.strftime('%Y-%m-%d %H:%M:%S'), completed_at.strftime('%Y-%m-%d %H:%M:%S')))
                db.execute("UPDATE needs SET status = 'fulfilled' WHERE id = ?", (need['id'],))
                db.execute("UPDATE offers SET status = 'completed' WHERE id = ?", (offer['id'],))
        db.commit()

        active_count = db.execute("SELECT COUNT(*) FROM matches WHERE status IN ('accepted', 'arrived', 'paid')").fetchone()[0]
        if active_count < 3:
            candidates = db.execute('''
                SELECT n.id AS need_id, o.id AS offer_id
                FROM needs n JOIN offers o ON o.category = n.category
                WHERE n.status = 'open' AND o.status = 'available'
                ORDER BY n.id, o.id LIMIT 12
            ''').fetchall()
            made = 0
            for row in candidates:
                if active_count + made >= 3:
                    break
                owner_match = db.execute('SELECT user_id FROM needs WHERE id = ?', (row['need_id'],)).fetchone()
                offer_match = db.execute('SELECT user_id FROM offers WHERE id = ?', (row['offer_id'],)).fetchone()
                if owner_match['user_id'] == offer_match['user_id']:
                    continue
                existing = db.execute('SELECT id FROM matches WHERE need_id = ? OR offer_id = ?', (row['need_id'], row['offer_id'])).fetchone()
                if existing:
                    continue
                status = ['accepted', 'arrived', 'paid'][made % 3]
                otp = str(100000 + made + 1)
                amount = 200 + made * 50 if status == 'paid' else None
                db.execute('''
                    INSERT INTO matches (need_id, offer_id, status, otp, otp_attempts, amount_paid, arrived_at, paid_at)
                    VALUES (?, ?, ?, ?, 0, ?, CASE WHEN ? IN ('arrived','paid') THEN CURRENT_TIMESTAMP ELSE NULL END, CASE WHEN ? = 'paid' THEN CURRENT_TIMESTAMP ELSE NULL END)
                ''', (row['need_id'], row['offer_id'], status, otp, amount, status, status))
                db.execute("UPDATE needs SET status = 'matched' WHERE id = ?", (row['need_id'],))
                db.execute("UPDATE offers SET status = 'matched' WHERE id = ?", (row['offer_id'],))
                made += 1
            db.commit()

        # Recompute demo impact from completed matches using the new 15/20 split.
        db.execute('''
            UPDATE users
            SET impact_points =
                COALESCE((SELECT COUNT(*) FROM matches m JOIN needs n ON n.id = m.need_id
                          WHERE m.status = 'completed' AND n.user_id = users.id), 0) * 15
                + COALESCE((SELECT COUNT(*) FROM matches m JOIN offers o ON o.id = m.offer_id
                            WHERE m.status = 'completed' AND o.user_id = users.id), 0) * 20
        ''')

        matches = db.execute('''
            SELECT m.id, n.user_id AS need_user_id, o.user_id AS offer_user_id
            FROM matches m JOIN needs n ON n.id = m.need_id JOIN offers o ON o.id = m.offer_id
            WHERE m.status = 'completed' ORDER BY m.id LIMIT 15
        ''').fetchall()
        for i, match in enumerate(matches):
            exists = db.execute('SELECT id FROM ratings WHERE match_id = ? LIMIT 1', (match['id'],)).fetchone()
            if exists:
                continue
            stars = 3 + (i % 3)
            db.execute('INSERT INTO ratings (match_id, rater_id, ratee_id, stars, comment) VALUES (?, ?, ?, ?, ?)', (match['id'], match['need_user_id'], match['offer_user_id'], stars, 'Helpful, kind, and easy to coordinate with.'))
            db.execute('INSERT INTO ratings (match_id, rater_id, ratee_id, stars, comment) VALUES (?, ?, ?, ?, ?)', (match['id'], match['offer_user_id'], match['need_user_id'], min(5, stars + (1 if i % 2 == 0 else 0)), 'Great communication and a clear community request.'))
            if i < 6:
                created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.execute('INSERT INTO messages (match_id, sender_id, body, created_at) VALUES (?, ?, ?, ?)', (match['id'], match['need_user_id'], 'Hi! Thanks for connecting through ShareCircle.', created))
                db.execute('INSERT INTO messages (match_id, sender_id, body, created_at) VALUES (?, ?, ?, ?)', (match['id'], match['offer_user_id'], 'Happy to help. Let us coordinate the details here.', created))
        db.commit()

        if db.execute('SELECT COUNT(*) FROM notifications').fetchone()[0] < 20:
            users = [row['id'] for row in db.execute('SELECT id FROM users ORDER BY id LIMIT 20').fetchall()]
            for user_id in users:
                db.execute('INSERT INTO notifications (user_id, type, body, link, read) VALUES (?, ?, ?, ?, 0)', (user_id, 'match_completed', 'A community match was completed and impact was added.', '/dashboard'))
        db.commit()

        totals = {
            name: db.execute(query).fetchone()[0]
            for name, query in {
                'users': 'SELECT COUNT(*) FROM users',
                'needs': 'SELECT COUNT(*) FROM needs',
                'offers': 'SELECT COUNT(*) FROM offers',
                'completed': "SELECT COUNT(*) FROM matches WHERE status='completed'",
                'active': "SELECT COUNT(*) FROM matches WHERE status IN ('accepted','arrived','paid')",
                'notifications': 'SELECT COUNT(*) FROM notifications',
            }.items()
        }
        print('ShareCircle seed complete:', totals)
        print(f'Demo login: username=asha password={SEED_PASSWORD}')


if __name__ == '__main__':
    main()
