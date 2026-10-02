import hashlib
import hmac
import os
import re

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from ..auth import login_required
from ..categories import CATEGORIES
from ..db import get_db
from ..matching import explain_match, find_best_matches

main_bp = Blueprint('main', __name__)


RESET_PASSWORD = os.environ.get('SHARECIRCLE_RESET_PASSWORD', 'ShareCircle123')


def _receipt_code_for_match(match_id, completed_at):
    completed_date = str(completed_at)[:10]
    return f"SC-{completed_date.replace('-', '')}-{int(match_id):04d}"


def _receipt_signature(receipt_code):
    secret = str(current_app.config.get('SECRET_KEY', 'sharecircle-local-dev-key-2026')).encode('utf-8')
    return hmac.new(secret, receipt_code.encode('utf-8'), hashlib.sha256).hexdigest()[:16]


def _avg_rating(user_id):
    row = get_db().execute(
        'SELECT COALESCE(AVG(stars), 0) AS avg_rating, COUNT(*) AS count FROM ratings WHERE ratee_id = ?',
        (user_id,),
    ).fetchone()
    return round(float(row['avg_rating'] or 0), 1), int(row['count'])


def _recommendations(need):
    db = get_db()
    rows = db.execute('''
        SELECT o.*, u.username, u.full_name,
               COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS average_rating
        FROM offers o JOIN users u ON u.id = o.user_id
        WHERE o.status = 'available'
        ORDER BY o.created_at DESC
    ''').fetchall()
    best = find_best_matches(need, rows, limit=5)
    result = []
    for row in best:
        breakdown = explain_match(need, row)
        result.append(dict(row, score=breakdown['total'], breakdown=breakdown))
    return result


def _avg_response_hours(user_id):
    row = get_db().execute('''
        SELECT AVG((julianday(m.created_at) - julianday(n.created_at)) * 24) AS avg_hours,
               COUNT(*) AS count
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN offers o ON o.id = m.offer_id
        WHERE o.user_id = ? AND m.status != 'cancelled'
    ''', (user_id,)).fetchone()
    if row['count'] == 0 or row['avg_hours'] is None:
        return None, 0
    return float(row['avg_hours']), int(row['count'])


def _trust_badges(helps_given, avg_rating, rating_count, avg_response_hours, response_count):
    """Compute reputation badges purely from data already on hand — no new
    tables, just thresholds over completed helps, ratings, and response time."""
    badges = []
    if helps_given >= 3 and rating_count >= 3 and avg_rating >= 4.0:
        badges.append({
            'key': 'verified_helper',
            'label': 'Verified Helper',
            'icon': '✓',
            'detail': f'{helps_given} completed helps, {avg_rating}★ average',
        })
    if helps_given >= 10:
        badges.append({
            'key': 'neighborhood_hero',
            'label': 'Neighborhood Hero',
            'icon': '⛨',
            'detail': f'{helps_given} neighbors helped',
        })
    if response_count >= 3 and avg_response_hours is not None and avg_response_hours <= 2:
        badges.append({
            'key': 'fast_responder',
            'label': 'Fast Responder',
            'icon': '⚡',
            'detail': f'Accepts needs in ~{round(avg_response_hours, 1)}h on average',
        })
    return badges


def _active_match_for_user(user_id):
    return get_db().execute('''
        SELECT m.id, m.status, m.created_at, m.arrived_at, m.paid_at, m.completed_at,
               m.amount_paid, m.otp_attempts,
               n.id AS need_id, n.title AS need_title, n.description AS need_description,
               n.category AS need_category, n.urgency AS need_urgency, n.price AS need_price,
               n.status AS need_status, n.lat AS need_lat, n.lng AS need_lng,
               nu.username AS need_username, nu.full_name AS need_full_name, nu.location AS need_location,
               o.id AS offer_id, o.title AS offer_title, o.description AS offer_description,
               o.category AS offer_category, o.availability AS offer_availability,
               o.status AS offer_status,
               ou.username AS offer_username, ou.full_name AS offer_full_name, ou.location AS offer_location
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN users nu ON nu.id = n.user_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users ou ON ou.id = o.user_id
        WHERE m.status IN ('accepted', 'arrived', 'paid')
          AND (n.user_id = ? OR o.user_id = ?)
        ORDER BY m.created_at DESC, m.id DESC
        LIMIT 1
    ''', (user_id, user_id)).fetchone()


@main_bp.get('/')
def home():
    db = get_db()
    stats = {
        'members': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'needs': db.execute('SELECT COUNT(*) FROM needs').fetchone()[0],
        'offers': db.execute('SELECT COUNT(*) FROM offers').fetchone()[0],
        'completed': db.execute("SELECT COUNT(*) FROM matches WHERE status = 'completed'").fetchone()[0],
    }
    recent_needs = db.execute('''
        SELECT n.id, n.title, n.category, n.urgency, n.price, n.created_at, u.location
        FROM needs n JOIN users u ON u.id = n.user_id
        WHERE n.status = 'open'
        ORDER BY n.created_at DESC LIMIT 6
    ''').fetchall()
    recent_completed = db.execute('''
        SELECT n.title AS need_title, o.title AS offer_title, m.completed_at
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN offers o ON o.id = m.offer_id
        WHERE m.status = 'completed'
        ORDER BY m.completed_at DESC LIMIT 6
    ''').fetchall()
    return render_template('home.html', stats=stats, recent_needs=recent_needs, recent_completed=recent_completed)


@main_bp.get('/judge')
def judge_mode():
    return render_template('main/judge.html')


@main_bp.get('/dashboard')
@login_required
def dashboard():
    db = get_db()
    needs = db.execute(
        'SELECT * FROM needs WHERE user_id = ? ORDER BY created_at DESC LIMIT 8',
        (g.user['id'],),
    ).fetchall()
    offers = db.execute(
        'SELECT * FROM offers WHERE user_id = ? ORDER BY created_at DESC LIMIT 8',
        (g.user['id'],),
    ).fetchall()
    matches = db.execute('''
        SELECT m.id, m.status, m.created_at, m.completed_at, m.arrived_at, m.paid_at, m.amount_paid,
               n.id AS need_id, n.title AS need_title, n.user_id AS need_user_id,
               o.id AS offer_id, o.title AS offer_title, o.user_id AS offer_user_id,
               nu.username AS need_username, nu.full_name AS need_full_name,
               ou.username AS offer_username, ou.full_name AS offer_full_name,
               (
                 SELECT COUNT(*) FROM messages msg
                 WHERE msg.match_id = m.id AND msg.sender_id != ? AND msg.created_at > COALESCE(
                   (SELECT messages_seen_at FROM users WHERE id = ?), '1970-01-01'
                 )
               ) AS unread_messages
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users nu ON nu.id = n.user_id
        JOIN users ou ON ou.id = o.user_id
        WHERE n.user_id = ? OR o.user_id = ?
        ORDER BY CASE WHEN m.status IN ('accepted', 'arrived', 'paid') THEN 0 ELSE 1 END,
                 m.created_at DESC LIMIT 12
    ''', (g.user['id'], g.user['id'], g.user['id'], g.user['id'])).fetchall()
    active_match = _active_match_for_user(g.user['id'])
    offer_categories = db.execute(
        "SELECT DISTINCT category FROM offers WHERE user_id = ? AND status IN ('available', 'matched') ORDER BY category",
        (g.user['id'],),
    ).fetchall()
    return render_template(
        'main/dashboard.html',
        needs=needs,
        offers=offers,
        matches=matches,
        active_match=active_match,
        offer_categories=[row['category'] for row in offer_categories],
    )


@main_bp.get('/nearby')
@login_required
def nearby():
    categories = get_db().execute(
        'SELECT DISTINCT category FROM offers WHERE user_id = ? ORDER BY category',
        (g.user['id'],),
    ).fetchall()
    return render_template('main/nearby.html', offer_categories=[row['category'] for row in categories])


@main_bp.get('/match/<int:match_id>')
@login_required
def match_view(match_id):
    db = get_db()
    match = db.execute('''
        SELECT m.id, m.status, m.created_at, m.arrived_at, m.paid_at, m.completed_at,
               m.amount_paid, m.otp_attempts,
               n.id AS need_id, n.title AS need_title, n.description AS need_description,
               n.category AS need_category, n.urgency AS need_urgency, n.lat AS need_lat, n.lng AS need_lng,
               nu.id AS need_user_id, nu.username AS need_username, nu.full_name AS need_full_name, nu.location AS need_location,
               o.id AS offer_id, o.title AS offer_title, o.description AS offer_description,
               o.category AS offer_category, o.availability AS offer_availability,
               ou.id AS offer_user_id, ou.username AS offer_username, ou.full_name AS offer_full_name,
               COALESCE((SELECT stars FROM ratings WHERE match_id = m.id AND rater_id = ? LIMIT 1), 0) AS viewer_rating
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN users nu ON nu.id = n.user_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users ou ON ou.id = o.user_id
        WHERE m.id = ? AND (n.user_id = ? OR o.user_id = ?)
    ''', (g.user['id'], match_id, g.user['id'], g.user['id'])).fetchone()
    if match is None:
        return render_template('404.html'), 404
    return render_template('main/match.html', match=match)


@main_bp.get('/browse')
def browse():
    return render_template('main/browse.html', categories=CATEGORIES)


@main_bp.get('/needs/new')
@login_required
def new_need():
    return render_template('main/need_form.html', categories=CATEGORIES, item=None)


@main_bp.get('/offers/new')
@login_required
def new_offer():
    return render_template('main/offer_form.html', categories=CATEGORIES, item=None)


@main_bp.get('/needs/<int:need_id>')
def need_detail(need_id):
    db = get_db()
    need = db.execute('''
        SELECT n.*, u.username, u.full_name, u.location
        FROM needs n JOIN users u ON u.id = n.user_id WHERE n.id = ?
    ''', (need_id,)).fetchone()
    if need is None:
        return render_template('404.html'), 404
    recommendations = _recommendations(need)
    return render_template('main/need_detail.html', need=need, recommendations=recommendations)


@main_bp.get('/offers/<int:offer_id>')
def offer_detail(offer_id):
    db = get_db()
    offer = db.execute('''
        SELECT o.*, u.username, u.full_name, u.location,
               COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS average_rating,
               COALESCE((SELECT COUNT(*) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS rating_count
        FROM offers o JOIN users u ON u.id = o.user_id WHERE o.id = ?
    ''', (offer_id,)).fetchone()
    if offer is None:
        return render_template('404.html'), 404
    return render_template('main/offer_detail.html', offer=offer)



@main_bp.get('/impact')
def impact():
    db = get_db()
    categories = db.execute('''
        SELECT n.category, COUNT(*) AS total
        FROM matches m JOIN needs n ON n.id = m.need_id
        WHERE m.status = 'completed'
        GROUP BY n.category ORDER BY total DESC LIMIT 5
    ''').fetchall()
    supply_demand_rows = db.execute('''
        WITH need_counts AS (
            SELECT category, COUNT(*) AS needs
            FROM needs
            WHERE status = 'open'
            GROUP BY category
        ),
        offer_counts AS (
            SELECT category, COUNT(*) AS offers
            FROM offers
            WHERE status = 'available'
            GROUP BY category
        ),
        category_totals AS (
            SELECT category FROM need_counts
            UNION
            SELECT category FROM offer_counts
        )
        SELECT c.category,
               COALESCE(n.needs, 0) AS needs,
               COALESCE(o.offers, 0) AS offers
        FROM category_totals c
        LEFT JOIN need_counts n ON n.category = c.category
        LEFT JOIN offer_counts o ON o.category = c.category
        ORDER BY
            CASE WHEN COALESCE(n.needs, 0) > 0
                 THEN CAST(COALESCE(o.offers, 0) AS REAL) / n.needs
                 ELSE 999999 END ASC,
            COALESCE(n.needs, 0) DESC,
            c.category ASC
    ''').fetchall()
    supply_demand = []
    for row in supply_demand_rows:
        needs = int(row['needs'])
        offers = int(row['offers'])
        ratio = round(offers / needs, 2) if needs else None
        supply_demand.append({
            'category': row['category'],
            'needs': needs,
            'offers': offers,
            'ratio': ratio,
            'coverage_percent': min(ratio, 2) / 2 * 100 if ratio is not None else 100,
            'helpers_needed': max(needs - offers, 0),
        })
    stats = {
        'members': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'needs': db.execute('SELECT COUNT(*) FROM needs').fetchone()[0],
        'offers': db.execute('SELECT COUNT(*) FROM offers').fetchone()[0],
        'completed': db.execute("SELECT COUNT(*) FROM matches WHERE status = 'completed'").fetchone()[0],
        'points': db.execute('SELECT COALESCE(SUM(impact_points), 0) FROM users').fetchone()[0],
    }
    return render_template(
        'main/impact.html',
        stats=stats,
        categories=categories,
        supply_demand=supply_demand,
    )


@main_bp.get('/match/<int:match_id>/receipt')
@login_required
def match_receipt(match_id):
    db = get_db()
    match = db.execute('''
        SELECT m.id, m.status, m.created_at, m.completed_at, m.amount_paid,
               n.title AS need_title, n.description AS need_description,
               n.category AS need_category, n.urgency AS need_urgency,
               nu.username AS need_username, nu.full_name AS need_full_name, nu.location AS need_location,
               o.title AS offer_title, o.description AS offer_description,
               ou.username AS offer_username, ou.full_name AS offer_full_name, ou.location AS offer_location
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN users nu ON nu.id = n.user_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users ou ON ou.id = o.user_id
        WHERE m.id = ?
          AND m.status = 'completed'
          AND (n.user_id = ? OR o.user_id = ?)
    ''', (match_id, g.user['id'], g.user['id'])).fetchone()
    if match is None:
        return render_template('404.html'), 404
    completed_at = match['completed_at'] or match['created_at']
    completed_date = str(completed_at)[:10]
    receipt_code = _receipt_code_for_match(match['id'], completed_at)
    verify_url = url_for('main.verify_receipt', receipt_code=receipt_code, sig=_receipt_signature(receipt_code), _external=True)
    return render_template(
        'main/receipt.html',
        match=match,
        receipt_code=receipt_code,
        completed_date=completed_date,
        verify_url=verify_url,
        helper_points=20,
        need_owner_points=15,
    )


@main_bp.get('/impact/verify/<receipt_code>')
def verify_receipt(receipt_code):
    signature = request.args.get('sig', '')
    if not signature or not hmac.compare_digest(signature, _receipt_signature(receipt_code)):
        return render_template('404.html'), 404
    code_match = re.fullmatch(r'SC-(\d{8})-(\d+)', receipt_code)
    if not code_match:
        return render_template('404.html'), 404
    try:
        match_id = int(code_match.group(2))
    except ValueError:
        return render_template('404.html'), 404
    db = get_db()
    match = db.execute('''
        SELECT m.id, m.status, m.completed_at, m.created_at, n.category AS category
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        WHERE m.id = ? AND m.status = 'completed'
    ''', (match_id,)).fetchone()
    if match is None:
        return render_template('404.html'), 404
    completed_at = match['completed_at'] or match['created_at']
    if _receipt_code_for_match(match['id'], completed_at) != receipt_code:
        return render_template('404.html'), 404
    return render_template(
        'main/verify_receipt.html',
        receipt_code=receipt_code,
        completed_date=str(completed_at)[:10],
        category=match['category'],
        impact_points=35,
    )


@main_bp.route('/reset-data', methods=['GET', 'POST'])
def reset_data():
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirmation = request.form.get('confirmation', '').strip().upper()
        if not hmac.compare_digest(password, RESET_PASSWORD):
            flash('Incorrect reset password.', 'error')
            return render_template('main/reset_data.html'), 403
        if confirmation != 'RESET ALL DATA':
            flash('Type RESET ALL DATA exactly to confirm.', 'error')
            return render_template('main/reset_data.html'), 400

        db = get_db()
        for table in ('notifications', 'ratings', 'messages', 'matches', 'offers', 'needs', 'users'):
            db.execute(f'DELETE FROM {table}')
        db.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('notifications', 'ratings', 'messages', 'matches', 'offers', 'needs', 'users')"
        )
        db.commit()
        flash('All ShareCircle data was reset. The database structure is unchanged.', 'success')
        return redirect(url_for('main.home'))
    return render_template('main/reset_data.html')


@main_bp.get('/leaderboard')
def leaderboard():
    users = get_db().execute('''
        SELECT username, full_name, location, impact_points,
               COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = users.id), 0) AS avg_rating
        FROM users ORDER BY impact_points DESC, created_at ASC LIMIT 20
    ''').fetchall()
    return render_template('main/leaderboard.html', users=users)


@main_bp.get('/profile/<username>')
def profile(username):
    db = get_db()
    user = db.execute('''
        SELECT id, full_name, username, location, impact_points, created_at
        FROM users WHERE username = ?
    ''', (username,)).fetchone()
    if user is None:
        return render_template('404.html'), 404
    avg_rating, rating_count = _avg_rating(user['id'])
    helps_given = db.execute('''
        SELECT COUNT(*) FROM matches m JOIN offers o ON o.id = m.offer_id
        WHERE m.status = 'completed' AND o.user_id = ?
    ''', (user['id'],)).fetchone()[0]
    helps_received = db.execute('''
        SELECT COUNT(*) FROM matches m JOIN needs n ON n.id = m.need_id
        WHERE m.status = 'completed' AND n.user_id = ?
    ''', (user['id'],)).fetchone()[0]
    avg_response_hours, response_count = _avg_response_hours(user['id'])
    trust_badges = _trust_badges(helps_given, avg_rating, rating_count, avg_response_hours, response_count)
    needs = db.execute(
        'SELECT id, title, category, urgency, status, created_at FROM needs WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user['id'],),
    ).fetchall()
    offers = db.execute(
        'SELECT id, title, category, availability, status, created_at FROM offers WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user['id'],),
    ).fetchall()
    activity = db.execute('''
        SELECT m.id, m.completed_at, n.title AS need_title, o.title AS offer_title
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN offers o ON o.id = m.offer_id
        WHERE m.status = 'completed' AND (n.user_id = ? OR o.user_id = ?)
        ORDER BY m.completed_at DESC LIMIT 8
    ''', (user['id'], user['id'])).fetchall()
    return render_template(
        'main/profile.html',
        user=user,
        avg_rating=avg_rating,
        rating_count=rating_count,
        helps_given=helps_given,
        helps_received=helps_received,
        trust_badges=trust_badges,
        needs=needs,
        offers=offers,
        activity=activity,
    )
