PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    location TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    impact_points INTEGER NOT NULL DEFAULT 0,
    messages_seen_at TIMESTAMP,
    lat REAL,
    lng REAL,
    last_location_at TIMESTAMP,
    is_hackathon INTEGER NOT NULL DEFAULT 0 CHECK (is_hackathon IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS needs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK (urgency IN ('low', 'medium', 'high')),
    price REAL NOT NULL DEFAULT 1 CHECK (price > 0),
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'matched', 'fulfilled')),
    lat REAL,
    lng REAL,
    start_time TEXT NOT NULL DEFAULT '09:00 AM',
    end_time TEXT NOT NULL DEFAULT '05:00 PM',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    availability TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'matched', 'completed')),
    lat REAL,
    lng REAL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    need_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'accepted' CHECK (status IN ('accepted', 'arrived', 'paid', 'completed', 'cancelled')),
    otp TEXT,
    otp_attempts INTEGER NOT NULL DEFAULT 0,
    amount_paid REAL,
    paid_at TIMESTAMP,
    arrived_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE (need_id, offer_id),
    FOREIGN KEY (need_id) REFERENCES needs(id) ON DELETE CASCADE,
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    rater_id INTEGER NOT NULL,
    ratee_id INTEGER NOT NULL,
    stars INTEGER NOT NULL CHECK (stars BETWEEN 1 AND 5),
    comment TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (match_id, rater_id),
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    FOREIGN KEY (rater_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ratee_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    body TEXT NOT NULL,
    link TEXT NOT NULL,
    read INTEGER NOT NULL DEFAULT 0 CHECK (read IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_needs_status_category ON needs(status, category);
CREATE INDEX IF NOT EXISTS idx_offers_status_category ON offers(status, category);
CREATE INDEX IF NOT EXISTS idx_messages_match ON messages(match_id, created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read, created_at);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_one_live_need ON matches(need_id) WHERE status <> 'cancelled';
CREATE INDEX IF NOT EXISTS idx_needs_location ON needs(lat, lng);
CREATE INDEX IF NOT EXISTS idx_users_location ON users(lat, lng);
CREATE INDEX IF NOT EXISTS idx_users_hackathon ON users(is_hackathon, created_at);
