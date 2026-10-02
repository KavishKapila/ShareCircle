PRAGMA foreign_keys = OFF;

ALTER TABLE users ADD COLUMN lat REAL;
ALTER TABLE users ADD COLUMN lng REAL;
ALTER TABLE users ADD COLUMN last_location_at TIMESTAMP;

CREATE TABLE matches_gig_new (
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

INSERT INTO matches_gig_new (
    id, need_id, offer_id, status, otp, otp_attempts, amount_paid, paid_at,
    arrived_at, created_at, completed_at
)
SELECT
    id,
    need_id,
    offer_id,
    CASE
        WHEN status = 'matched' THEN 'cancelled'
        WHEN status = 'completed' THEN 'completed'
        ELSE 'cancelled'
    END,
    NULL,
    0,
    NULL,
    NULL,
    NULL,
    created_at,
    completed_at
FROM matches;

DROP TABLE matches;
ALTER TABLE matches_gig_new RENAME TO matches;

CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status, created_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_matches_one_live_need ON matches(need_id) WHERE status <> 'cancelled';
CREATE INDEX IF NOT EXISTS idx_needs_location ON needs(lat, lng);
CREATE INDEX IF NOT EXISTS idx_users_location ON users(lat, lng);

PRAGMA foreign_keys = ON;
