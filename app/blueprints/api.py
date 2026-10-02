import math
import re
import secrets
import sqlite3

from flask import Blueprint, g, jsonify, request, url_for
from ..auth import api_login_required
from ..categories import CATEGORIES, URGENCIES
from ..db import get_db
from ..integrations import process_donation, send_email, send_sms
from ..matching import explain_match, find_best_matches
from ..notifications import create_notification, unread_count

api_bp = Blueprint('api', __name__)

ACTIVE_MATCH_STATUSES = ('accepted', 'arrived', 'paid')
URGENT_ALERT_RADIUS_KM = 15
URGENT_ALERT_MAX_RECIPIENTS = 25


def _json_rows(rows):
    return [dict(row) for row in rows]


def _now_user_location(payload):
    try:
        lat = float(payload.get('lat'))
        lng = float(payload.get('lng'))
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def _haversine_km(lat1, lng1, lat2, lng2):
    earth_radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return earth_radius_km * 2 * math.asin(math.sqrt(min(1.0, a)))


def _bearing_deg(lat1, lng1, lat2, lng2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lambda = math.radians(lng2 - lng1)
    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _get_match_for_user(match_id):
    return get_db().execute('''
        SELECT m.*, n.user_id AS need_user_id, o.user_id AS offer_user_id,
               n.title AS need_title, n.description AS need_description,
               n.category AS need_category, n.urgency AS need_urgency, n.price AS need_price,
               n.status AS need_status, n.lat AS need_lat, n.lng AS need_lng,
               nu.username AS need_username, nu.full_name AS need_full_name,
               nu.location AS need_location,
               o.title AS offer_title, o.description AS offer_description,
               o.category AS offer_category, o.availability AS offer_availability,
               o.status AS offer_status, o.lat AS offer_lat, o.lng AS offer_lng,
               ou.username AS offer_username, ou.full_name AS offer_full_name,
               ou.location AS offer_location
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN users nu ON nu.id = n.user_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users ou ON ou.id = o.user_id
        WHERE m.id = ? AND (n.user_id = ? OR o.user_id = ?)
    ''', (match_id, g.user['id'], g.user['id'])).fetchone()


def _match_payload(match):
    caller_is_need_owner = g.user['id'] == match['need_user_id']
    caller_is_offer_owner = g.user['id'] == match['offer_user_id']
    payload = {
        'id': match['id'],
        'status': match['status'],
        'created_at': match['created_at'],
        'arrived_at': match['arrived_at'],
        'paid_at': match['paid_at'],
        'completed_at': match['completed_at'],
        'amount_paid': match['amount_paid'],
        'otp_attempts': match['otp_attempts'],
        'otp_locked': int(match['otp_attempts'] or 0) >= 3,
        'viewer_role': 'need_owner' if caller_is_need_owner else 'offerer',
        'viewer_rating': int(get_db().execute(
            'SELECT COALESCE(MAX(stars), 0) FROM ratings WHERE match_id = ? AND rater_id = ?',
            (match['id'], g.user['id'])
        ).fetchone()[0] or 0),
        'need': {
            'id': match['need_id'],
            'user_id': match['need_user_id'],
            'username': match['need_username'],
            'full_name': match['need_full_name'],
            'location': match['need_location'],
            'title': match['need_title'],
            'description': match['need_description'],
            'category': match['need_category'],
            'urgency': match['need_urgency'],
            'price': match['need_price'],
            'status': match['need_status'],
            'lat': match['need_lat'],
            'lng': match['need_lng'],
        },
        'offer': {
            'id': match['offer_id'],
            'user_id': match['offer_user_id'],
            'username': match['offer_username'],
            'full_name': match['offer_full_name'],
            'location': match['offer_location'],
            'title': match['offer_title'],
            'description': match['offer_description'],
            'category': match['offer_category'],
            'availability': match['offer_availability'],
            'status': match['offer_status'],
            'lat': match['offer_lat'],
            'lng': match['offer_lng'],
        },
    }
    if caller_is_need_owner and match['status'] == 'paid':
        payload['otp'] = match['otp']
    else:
        payload['otp'] = None
    return payload


def _notify_match_parties(match_id, need_user_id, offer_user_id, message, event_type, exclude_user_id=None):
    link = url_for('main.match_view', match_id=match_id)
    for user_id in (need_user_id, offer_user_id):
        if exclude_user_id is not None and user_id == exclude_user_id:
            continue
        create_notification(user_id, event_type, message, link)


def _generate_otp():
    return str(secrets.randbelow(900000) + 100000)


def _notify_nearby_offerers_of_urgent_need(need):
    """Proactively alert helpers whose available offers match a brand-new
    high-urgency need, instead of waiting for them to stumble onto it in
    Browse or Nearby. Scoped to the need's category and, when both sides
    have coordinates, to a short radius so alerts stay locally relevant.
    """
    if need['urgency'] != 'high':
        return
    db = get_db()
    candidates = db.execute('''
        SELECT DISTINCT u.id AS user_id, u.lat AS lat, u.lng AS lng
        FROM offers o
        JOIN users u ON u.id = o.user_id
        WHERE o.status = 'available' AND o.category = ? AND u.id != ?
    ''', (need['category'], need['user_id'])).fetchall()
    if not candidates:
        return
    link = url_for('main.need_detail', need_id=need['id'])
    message = f'Urgent {need["category"]} need posted near you: “{need["title"]}”.'
    notified = 0
    for row in candidates:
        if notified >= URGENT_ALERT_MAX_RECIPIENTS:
            break
        if (
            need['lat'] is not None and need['lng'] is not None
            and row['lat'] is not None and row['lng'] is not None
        ):
            distance = _haversine_km(need['lat'], need['lng'], row['lat'], row['lng'])
            if distance > URGENT_ALERT_RADIUS_KM:
                continue
        create_notification(row['user_id'], 'urgent_need_nearby', message, link)
        notified += 1


@api_bp.get('/health')
def health():
    get_db().execute('SELECT 1').fetchone()
    return jsonify({'status': 'ok', 'db': 'ok', 'version': '1.0'})


@api_bp.post('/location')
@api_login_required
def update_location():
    coords = _now_user_location(request.get_json(silent=True) or {})
    if coords is None:
        return jsonify({'error': 'Valid latitude and longitude are required.'}), 400
    db = get_db()
    db.execute(
        'UPDATE users SET lat = ?, lng = ?, last_location_at = CURRENT_TIMESTAMP WHERE id = ?',
        (coords[0], coords[1], g.user['id']),
    )
    db.commit()
    return jsonify({'lat': coords[0], 'lng': coords[1], 'updated': True})


@api_bp.post('/location/manual')
@api_login_required
def update_manual_location():
    payload = request.get_json(silent=True) or {}
    location = str(payload.get('location', '')).strip()
    if len(location) < 2 or len(location) > 120:
        return jsonify({'error': 'Enter a location between 2 and 120 characters.'}), 400
    db = get_db()
    db.execute(
        'UPDATE users SET location = ?, lat = NULL, lng = NULL, last_location_at = CURRENT_TIMESTAMP WHERE id = ?',
        (location, g.user['id']),
    )
    db.commit()
    return jsonify({'location': location, 'mode': 'manual', 'updated': True})




@api_bp.get('/auth/username-availability')
def username_availability():
    username = request.args.get('username', '').strip()
    if len(username) < 3:
        return jsonify({'available': False, 'valid': False, 'message': 'Use at least 3 characters.'})
    if not all(ch.isalnum() or ch in '._-' for ch in username):
        return jsonify({'available': False, 'valid': False, 'message': 'Use letters, numbers, dots, hyphens, or underscores.'})
    exists = get_db().execute('SELECT 1 FROM users WHERE username = ? COLLATE NOCASE LIMIT 1', (username,)).fetchone()
    return jsonify({'available': exists is None, 'valid': True, 'message': 'Username is available.' if exists is None else 'That username is already taken.'})


@api_bp.get('/form-insights')
@api_login_required
def form_insights():
    category = request.args.get('category', '').strip()
    title = request.args.get('title', '').strip().lower()
    description = request.args.get('description', '').strip().lower()
    text = f'{title} {description}'
    keyword_map = {
        'Education': ('tutor', 'teach', 'homework', 'math', 'study', 'class', 'exam'),
        'Food': ('meal', 'food', 'cook', 'lunch', 'dinner', 'grocer'),
        'Health': ('doctor', 'medicine', 'health', 'clinic', 'care'),
        'Elderly Care': ('elder', 'senior', 'older', 'grandma', 'grandpa', 'care'),
        'Clothing': ('clothes', 'shirt', 'dress', 'jacket', 'uniform'),
        'Mentorship': ('mentor', 'career', 'resume', 'interview', 'advice'),
        'Transport': ('ride', 'drive', 'bus', 'airport', 'transport'),
        'Other': (),
    }
    suggested_category = category if category in CATEGORIES else None
    if not suggested_category:
        scores = {cat: sum(1 for word in words if word in text) for cat, words in keyword_map.items()}
        suggested_category = max(scores, key=scores.get) if max(scores.values(), default=0) else None
    title_suggestions = []
    templates = {
        'Education': 'Looking for help with tutoring', 'Food': 'Looking for a meal or groceries',
        'Health': 'Need help with a health-related task', 'Elderly Care': 'Need a hand with elderly care',
        'Clothing': 'Looking for clothing support', 'Mentorship': 'Looking for a mentor',
        'Transport': 'Need a ride nearby', 'Other': 'Looking for a helping hand'
    }
    if suggested_category and len(title) < 12:
        title_suggestions.append(templates[suggested_category])
    db = get_db()
    params = []
    query = "SELECT o.lat, o.lng FROM offers o WHERE o.status = 'available'"
    if suggested_category in CATEGORIES:
        query += ' AND o.category = ?'
        params.append(suggested_category)
    offers = db.execute(query, params).fetchall()
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
    except (TypeError, ValueError):
        lat = lng = None
    if lat is not None and lng is not None:
        offers = [o for o in offers if o['lat'] is not None and o['lng'] is not None and _haversine_km(lat, lng, o['lat'], o['lng']) <= 15]
    return jsonify({'suggested_category': suggested_category, 'title_suggestions': title_suggestions, 'helper_count': len(offers)})


@api_bp.get('/stats')
@api_login_required
def stats():
    db = get_db()
    return jsonify({
        'members': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'needs': db.execute('SELECT COUNT(*) FROM needs').fetchone()[0],
        'offers': db.execute('SELECT COUNT(*) FROM offers').fetchone()[0],
        'completed': db.execute("SELECT COUNT(*) FROM matches WHERE status = 'completed'").fetchone()[0],
        'points': db.execute('SELECT COALESCE(SUM(impact_points), 0) FROM users').fetchone()[0],
    })


@api_bp.route('/needs', methods=['GET', 'POST'])
@api_login_required
def needs_api():
    db = get_db()
    if request.method == 'GET':
        q = request.args.get('q', '').strip().lower()
        category = request.args.get('category', '').strip()
        urgency = request.args.get('urgency', '').strip().lower()
        sort = request.args.get('sort', 'newest').strip()
        query = '''SELECT n.*, u.username, u.full_name, u.location,
                          (SELECT COUNT(*) FROM matches m WHERE m.need_id = n.id) AS match_count
                   FROM needs n JOIN users u ON u.id = n.user_id
                   WHERE n.status != 'fulfilled' '''
        params = []
        if q:
            query += 'AND (LOWER(n.title) LIKE ? OR LOWER(n.description) LIKE ?) '
            term = f'%{q}%'
            params.extend([term, term])
        if category in CATEGORIES:
            query += 'AND n.category = ? '
            params.append(category)
        if urgency in URGENCIES:
            query += 'AND n.urgency = ? '
            params.append(urgency)
        if sort == 'urgency':
            query += "ORDER BY CASE n.urgency WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, n.created_at DESC"
        elif sort == 'matched':
            query += 'ORDER BY match_count DESC, n.created_at DESC'
        else:
            query += 'ORDER BY n.created_at DESC'
        rows = db.execute(query, params).fetchall()
        return jsonify({'items': _json_rows(rows), 'count': len(rows)})

    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title', '')).strip()
    description = str(payload.get('description', '')).strip()
    category = str(payload.get('category', '')).strip()
    urgency = str(payload.get('urgency', '')).strip().lower()
    try:
        price = round(float(payload.get('price')), 2)
    except (TypeError, ValueError):
        price = 0
    lat = payload.get('lat')
    lng = payload.get('lng')
    location = str(payload.get('location', '')).strip()[:120]
    start_time = str(payload.get('start_time', '')).strip().upper()
    end_time = str(payload.get('end_time', '')).strip().upper()
    time_pattern = re.compile(r'^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM)$')
    if lat is not None and lng is not None:
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            lat = lng = None
    if lat is not None and lng is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180):
        lat = lng = None
    errors = []
    if len(title) < 3:
        errors.append('Title must be at least 3 characters.')
    if len(description) < 10:
        errors.append('Description must be at least 10 characters.')
    if category not in CATEGORIES:
        errors.append('Choose a valid category.')
    if urgency not in URGENCIES:
        errors.append('Choose a valid urgency.')
    if price <= 0 or price > 1000000:
        errors.append('Set a price between ₹1 and ₹10,00,000.')
    if not time_pattern.fullmatch(start_time):
        errors.append('Start time must include AM or PM, for example 4:00 PM.')
    if not time_pattern.fullmatch(end_time):
        errors.append('End time must include AM or PM, for example 7:00 PM.')
    if time_pattern.fullmatch(start_time) and time_pattern.fullmatch(end_time):
        def _minutes(value):
            hm, meridiem = value.split()
            hour, minute = map(int, hm.split(':'))
            if meridiem == 'AM':
                hour = 0 if hour == 12 else hour
            else:
                hour = 12 if hour == 12 else hour + 12
            return hour * 60 + minute
        if _minutes(end_time) <= _minutes(start_time):
            errors.append('End time must be later than start time.')
    if errors:
        return jsonify({'error': 'Validation failed.', 'fields': errors}), 400
    if location and location != 'Device location':
        db.execute('UPDATE users SET location = ?, last_location_at = CURRENT_TIMESTAMP WHERE id = ?', (location, g.user['id']))
    cursor = db.execute('''
        INSERT INTO needs (user_id, title, description, category, urgency, price, lat, lng, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (g.user['id'], title, description, category, urgency, price, lat, lng, start_time, end_time))
    db.commit()
    new_need = db.execute('SELECT * FROM needs WHERE id = ?', (cursor.lastrowid,)).fetchone()
    _notify_nearby_offerers_of_urgent_need(new_need)
    return jsonify({'item': dict(new_need), 'redirect_url': url_for('main.need_detail', need_id=new_need['id'])}), 201


@api_bp.post('/needs/<int:need_id>/close')
@api_login_required
def close_need(need_id):
    db=get_db(); row=db.execute('SELECT id,status FROM needs WHERE id=? AND user_id=?',(need_id,g.user['id'])).fetchone()
    if row is None: return jsonify({'error':'Need not found.'}),404
    if row['status']=='matched': return jsonify({'error':'You cannot close a matched need.'}),409
    db.execute("UPDATE needs SET status='fulfilled' WHERE id=?",(need_id,)); db.commit(); return jsonify({'ok':True})

@api_bp.post('/offers/<int:offer_id>/close')
@api_login_required
def close_offer(offer_id):
    db=get_db(); row=db.execute('SELECT id,status FROM offers WHERE id=? AND user_id=?',(offer_id,g.user['id'])).fetchone()
    if row is None: return jsonify({'error':'Offer not found.'}),404
    if row['status']=='matched': return jsonify({'error':'You cannot close a matched offer.'}),409
    db.execute("UPDATE offers SET status='completed' WHERE id=?",(offer_id,)); db.commit(); return jsonify({'ok':True})

@api_bp.post('/needs/<int:need_id>/delete')
@api_login_required
def delete_need(need_id):
    db=get_db(); row=db.execute('SELECT id,status FROM needs WHERE id=? AND user_id=?',(need_id,g.user['id'])).fetchone()
    if row is None: return jsonify({'error':'Need not found.'}),404
    if row['status']=='matched': return jsonify({'error':'Cancel the active match before deleting this need.'}),409
    db.execute('DELETE FROM needs WHERE id=?',(need_id,)); db.commit(); return jsonify({'ok':True})

@api_bp.post('/offers/<int:offer_id>/delete')
@api_login_required
def delete_offer(offer_id):
    db=get_db(); row=db.execute('SELECT id,status FROM offers WHERE id=? AND user_id=?',(offer_id,g.user['id'])).fetchone()
    if row is None: return jsonify({'error':'Offer not found.'}),404
    if row['status']=='matched': return jsonify({'error':'Cancel the active match before deleting this offer.'}),409
    db.execute('DELETE FROM offers WHERE id=?',(offer_id,)); db.commit(); return jsonify({'ok':True})

@api_bp.route('/offers', methods=['GET', 'POST'])
@api_login_required
def offers_api():
    db = get_db()
    if request.method == 'GET':
        q = request.args.get('q', '').strip().lower()
        category = request.args.get('category', '').strip()
        sort = request.args.get('sort', 'newest').strip()
        query = '''SELECT o.*, u.username, u.full_name, u.location,
                          (SELECT COUNT(*) FROM matches m WHERE m.offer_id = o.id) AS match_count,
                          COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS average_rating
                   FROM offers o JOIN users u ON u.id = o.user_id
                   WHERE o.status = 'available' '''
        params = []
        if q:
            query += 'AND (LOWER(o.title) LIKE ? OR LOWER(o.description) LIKE ?) '
            term = f'%{q}%'
            params.extend([term, term])
        if category in CATEGORIES:
            query += 'AND o.category = ? '
            params.append(category)
        if sort == 'matched':
            query += 'ORDER BY match_count DESC, o.created_at DESC'
        else:
            query += 'ORDER BY o.created_at DESC'
        return jsonify({'items': _json_rows(db.execute(query, params).fetchall())})

    payload = request.get_json(silent=True) or {}
    title = str(payload.get('title', '')).strip()
    description = str(payload.get('description', '')).strip()
    category = str(payload.get('category', '')).strip()
    availability = str(payload.get('availability', '')).strip()
    lat = payload.get('lat')
    lng = payload.get('lng')
    location = str(payload.get('location', '')).strip()[:120]
    if lat is not None and lng is not None:
        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            lat = lng = None
    if lat is not None and lng is not None and not (-90 <= lat <= 90 and -180 <= lng <= 180):
        lat = lng = None
    errors = []
    if len(title) < 3:
        errors.append('Title must be at least 3 characters.')
    if len(description) < 10:
        errors.append('Description must be at least 10 characters.')
    if category not in CATEGORIES:
        errors.append('Choose a valid category.')
    if len(availability) < 2:
        errors.append('Add availability details.')
    if errors:
        return jsonify({'error': 'Validation failed.', 'fields': errors}), 400
    if location and location != 'Device location':
        db.execute('UPDATE users SET location = ?, last_location_at = CURRENT_TIMESTAMP WHERE id = ?', (location, g.user['id']))
    cursor = db.execute('''
        INSERT INTO offers (user_id, title, description, category, availability, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (g.user['id'], title, description, category, availability, lat, lng))
    db.commit()
    new_offer = db.execute('SELECT * FROM offers WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return jsonify({'item': dict(new_offer), 'redirect_url': url_for('main.offer_detail', offer_id=new_offer['id'])}), 201


@api_bp.get('/needs/nearby')
@api_login_required
def nearby_needs():
    manual_location = request.args.get('location', '').strip()[:120]
    raw_lat = request.args.get('lat')
    raw_lng = request.args.get('lng')
    try:
        lat = float(raw_lat) if raw_lat is not None else float(g.user['lat'])
        lng = float(raw_lng) if raw_lng is not None else float(g.user['lng'])
    except (TypeError, ValueError):
        lat = lng = None

    try:
        radius_km = float(request.args.get('radius_km', 10))
    except (TypeError, ValueError):
        radius_km = 10
    radius_km = max(0.5, min(radius_km, 50))

    db = get_db()
    category_rows = db.execute(
        'SELECT DISTINCT category FROM offers WHERE user_id = ?',
        (g.user['id'],),
    ).fetchall()
    categories = [row['category'] for row in category_rows]
    placeholders = ','.join('?' for _ in categories)

    if not categories:
        return jsonify({
            'items': [], 'categories': [], 'lat': lat, 'lng': lng,
            'radius_km': radius_km,
            'location_mode': 'manual' if manual_location else ('coordinates' if lat is not None else 'manual'),
            'location': manual_location or g.user['location'],
        })

    # Manual mode matches the location text already shown on member profiles.
    # It avoids sending a typed address to a third-party geocoding service.
    match_location = manual_location or (str(g.user['location'] or '').strip() if lat is None or lng is None else '')
    if match_location:
        rows = db.execute(f'''
            SELECT n.*, u.username, u.full_name, u.location
            FROM needs n
            JOIN users u ON u.id = n.user_id
            WHERE n.status = 'open'
              AND n.category IN ({placeholders})
              AND LOWER(u.location) LIKE LOWER(?)
        ''', (*categories, f'%{match_location}%')).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item['distance_km'] = None
            item['bearing_deg'] = None
            item['time_posted'] = 'Posted recently'
            item['match_reason'] = f'Matches your {row["category"]} offer in this area.'
            items.append(item)
        urgency_rank = {'high': 3, 'medium': 2, 'low': 1}
        items.sort(key=lambda item: (-urgency_rank.get(item['urgency'], 0), -int(item['id'])))
        return jsonify({
            'items': items,
            'categories': categories,
            'lat': None,
            'lng': None,
            'radius_km': radius_km,
            'location_mode': 'manual',
            'location': match_location,
        })

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify({'error': 'Invalid map coordinates.'}), 400

    rows = db.execute(f'''
        SELECT n.*, u.username, u.full_name, u.location
        FROM needs n
        JOIN users u ON u.id = n.user_id
        WHERE n.status = 'open'
          AND n.category IN ({placeholders})
          AND n.lat IS NOT NULL AND n.lng IS NOT NULL
    ''', categories).fetchall()

    items = []
    for row in rows:
        distance = _haversine_km(lat, lng, float(row['lat']), float(row['lng']))
        if distance <= radius_km:
            item = dict(row)
            item['distance_km'] = round(distance, 2)
            item['bearing_deg'] = round(_bearing_deg(lat, lng, float(row['lat']), float(row['lng'])), 1)
            item['time_posted'] = 'Posted recently'
            item['match_reason'] = f'Matches your {row["category"]} offer and nearby feed.'
            items.append(item)

    urgency_rank = {'high': 3, 'medium': 2, 'low': 1}
    items.sort(key=lambda item: (item['distance_km'], -urgency_rank.get(item['urgency'], 0), -int(item['id'])))
    return jsonify({
        'items': items,
        'categories': categories,
        'lat': lat,
        'lng': lng,
        'radius_km': radius_km,
        'location_mode': 'coordinates',
        'location': g.user['location'],
    })


@api_bp.get('/needs/<int:need_id>/matches')
@api_login_required
def suggested_matches(need_id):
    db = get_db()
    need = db.execute('SELECT * FROM needs WHERE id = ? AND user_id = ?', (need_id, g.user['id'])).fetchone()
    if need is None:
        return jsonify({'error': 'Need not found or not owned by you.'}), 404
    rows = db.execute('''
        SELECT o.*, u.username, u.full_name,
               COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS average_rating
        FROM offers o JOIN users u ON u.id = o.user_id
        WHERE o.status = 'available'
    ''').fetchall()
    items = []
    for offer in find_best_matches(need, rows, limit=5):
        items.append(dict(offer, breakdown=explain_match(need, offer)))
    return jsonify({'items': items})


@api_bp.post('/matches')
@api_login_required
def create_match():
    payload = request.get_json(silent=True) or {}
    need_id = payload.get('need_id')
    db = get_db()
    need = db.execute('SELECT * FROM needs WHERE id = ?', (need_id,)).fetchone()
    if need is None:
        return jsonify({'error': 'Need not found.'}), 404
    if need['user_id'] == g.user['id']:
        return jsonify({'error': 'You cannot accept your own need.'}), 403
    if need['status'] != 'open':
        return jsonify({'error': 'That need is no longer available.'}), 409

    offers = db.execute('''
        SELECT o.*, u.username, u.full_name,
               COALESCE((SELECT AVG(r.stars) FROM ratings r WHERE r.ratee_id = o.user_id), 0) AS average_rating
        FROM offers o
        JOIN users u ON u.id = o.user_id
        WHERE o.user_id = ? AND o.status = 'available' AND o.category = ?
    ''', (g.user['id'], need['category'])).fetchall()
    best = find_best_matches(need, offers, limit=1)
    if not best:
        return jsonify({'error': f'You do not have an available {need["category"]} offer. Post one first.'}), 409
    offer = best[0]

    existing = db.execute(
        "SELECT id FROM matches WHERE need_id = ? AND status != 'cancelled'",
        (need_id,),
    ).fetchone()
    if existing:
        return jsonify({'error': 'That need has already been accepted.'}), 409

    otp = _generate_otp()
    try:
        cursor = db.execute('''
            INSERT INTO matches (need_id, offer_id, status, otp, otp_attempts)
            VALUES (?, ?, 'accepted', ?, 0)
        ''', (need_id, offer['id'], otp))
        db.execute("UPDATE needs SET status = 'matched' WHERE id = ?", (need_id,))
        db.execute("UPDATE offers SET status = 'matched' WHERE id = ?", (offer['id'],))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({'error': 'That need is no longer available.'}), 409

    match_id = cursor.lastrowid
    link = url_for('main.match_view', match_id=match_id)
    create_notification(
        need['user_id'],
        'match_created',
        f'{g.user["full_name"]} accepted your need. Your verification OTP is ready on your dashboard after payment.',
        link,
    )
    create_notification(
        g.user['id'],
        'match_created',
        f'You accepted “{need["title"]}”. Open the match to navigate there.',
        link,
    )
    send_sms('', f'A ShareCircle helper accepted your need. Your OTP is stored securely in your dashboard.')
    send_email('', 'ShareCircle match accepted', f'A helper accepted need #{need_id}.')
    return jsonify({'id': match_id, 'status': 'accepted', 'need_id': need_id, 'offer_id': offer['id']}), 201


@api_bp.get('/matches/active')
@api_login_required
def active_match():
    placeholders = ','.join('?' for _ in ACTIVE_MATCH_STATUSES)
    match = get_db().execute(f'''
        SELECT m.*, n.user_id AS need_user_id, o.user_id AS offer_user_id,
               n.title AS need_title, n.description AS need_description,
               n.category AS need_category, n.urgency AS need_urgency, n.price AS need_price,
               n.status AS need_status, n.lat AS need_lat, n.lng AS need_lng,
               nu.username AS need_username, nu.full_name AS need_full_name, nu.location AS need_location,
               o.title AS offer_title, o.description AS offer_description,
               o.category AS offer_category, o.availability AS offer_availability,
               o.status AS offer_status, o.lat AS offer_lat, o.lng AS offer_lng,
               ou.username AS offer_username, ou.full_name AS offer_full_name, ou.location AS offer_location
        FROM matches m
        JOIN needs n ON n.id = m.need_id
        JOIN users nu ON nu.id = n.user_id
        JOIN offers o ON o.id = m.offer_id
        JOIN users ou ON ou.id = o.user_id
        WHERE m.status IN ({placeholders}) AND (n.user_id = ? OR o.user_id = ?)
        ORDER BY m.created_at DESC, m.id DESC
        LIMIT 1
    ''', (*ACTIVE_MATCH_STATUSES, g.user['id'], g.user['id'])).fetchone()
    if match is None:
        return jsonify({'match': None})
    return jsonify({'match': _match_payload(match)})


@api_bp.get('/matches/<int:match_id>')
@api_login_required
def match_detail_api(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    return jsonify({'match': _match_payload(match)})


@api_bp.post('/matches/<int:match_id>/arrive')
@api_login_required
def arrive_match(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['offer_user_id'] != g.user['id']:
        return jsonify({'error': 'Only the helper can mark arrival.'}), 403
    if match['status'] != 'accepted':
        return jsonify({'error': 'This match is not waiting for arrival.'}), 409
    db = get_db()
    cursor = db.execute("UPDATE matches SET status = 'arrived', arrived_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'accepted'", (match_id,))
    if cursor.rowcount != 1:
        db.rollback()
        return jsonify({'error': 'This match is not waiting for arrival.'}), 409
    db.commit()
    message = f'{g.user["full_name"]} has arrived for “{match["need_title"]}”.'
    _notify_match_parties(match_id, match['need_user_id'], match['offer_user_id'], message, 'match_arrived', exclude_user_id=g.user['id'])
    create_notification(g.user['id'], 'match_arrived', 'You marked the match as arrived. Deliver the service, then ask for payment.', url_for('main.match_view', match_id=match_id))
    return jsonify({'status': 'arrived'})


@api_bp.post('/matches/<int:match_id>/pay')
@api_login_required
def pay_match(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['need_user_id'] != g.user['id']:
        return jsonify({'error': 'Only the need owner can record payment.'}), 403
    if match['status'] != 'arrived':
        return jsonify({'error': 'Payment can be recorded after the helper arrives.'}), 409
    payload = request.get_json(silent=True) or {}
    try:
        amount = float(payload.get('amount'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Enter a valid payment amount.'}), 400
    if not math.isfinite(amount) or amount <= 0 or amount > 1000000:
        return jsonify({'error': 'Payment amount must be greater than ₹0 and within the allowed range.'}), 400
    amount = round(amount, 2)
    db = get_db()
    cursor = db.execute("UPDATE matches SET status = 'paid', amount_paid = ?, paid_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'arrived'", (amount, match_id))
    if cursor.rowcount != 1:
        db.rollback()
        return jsonify({'error': 'This match is no longer waiting for payment.'}), 409
    db.commit()
    create_notification(
        match['offer_user_id'],
        'payment_received',
        f'Payment of ₹{amount:.2f} was recorded. Ask the need owner for the OTP to complete the match.',
        url_for('main.match_view', match_id=match_id),
    )
    create_notification(
        match['need_user_id'],
        'payment_received',
        f'Payment recorded. Show the OTP to your helper when they are ready to finish.',
        url_for('main.match_view', match_id=match_id),
    )
    process_donation(amount, 'INR-off-app')
    return jsonify({'status': 'paid', 'amount_paid': amount})


@api_bp.post('/matches/<int:match_id>/complete')
@api_login_required
def complete_match(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['offer_user_id'] != g.user['id']:
        return jsonify({'error': 'Only the helper can complete this match.'}), 403
    if match['status'] != 'paid':
        return jsonify({'error': 'The need owner must record payment before completion.'}), 409
    if int(match['otp_attempts'] or 0) >= 3:
        return jsonify({'error': 'OTP locked. Ask the need owner to resend a new OTP.'}), 409
    payload = request.get_json(silent=True) or {}
    otp = str(payload.get('otp', '')).strip()
    if not otp or not otp.isdigit() or len(otp) != 6:
        return jsonify({'error': 'Enter the 6-digit OTP.'}), 400
    db = get_db()
    if otp != match['otp']:
        cursor = db.execute(
            "UPDATE matches SET otp_attempts = otp_attempts + 1 WHERE id = ? AND status = 'paid' AND otp_attempts < 3",
            (match_id,),
        )
        if cursor.rowcount != 1:
            db.rollback()
            return jsonify({'error': 'OTP locked. Ask the need owner to resend a new OTP.'}), 409
        attempts = db.execute('SELECT otp_attempts FROM matches WHERE id = ?', (match_id,)).fetchone()['otp_attempts']
        db.commit()
        if attempts >= 3:
            return jsonify({'error': 'Incorrect OTP', 'attempts_remaining': 0, 'otp_locked': True}), 400
        return jsonify({'error': 'Incorrect OTP', 'attempts_remaining': 3 - attempts, 'otp_locked': False}), 400

    cursor = db.execute(
        "UPDATE matches SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'paid' AND otp_attempts < 3",
        (match_id,),
    )
    if cursor.rowcount != 1:
        db.rollback()
        return jsonify({'error': 'This match has already been completed or its OTP is locked.'}), 409
    db.execute("UPDATE needs SET status = 'fulfilled' WHERE id = ?", (match['need_id'],))
    db.execute("UPDATE offers SET status = 'completed' WHERE id = ?", (match['offer_id'],))
    db.execute('UPDATE users SET impact_points = impact_points + 15 WHERE id = ?', (match['need_user_id'],))
    db.execute('UPDATE users SET impact_points = impact_points + 20 WHERE id = ?', (match['offer_user_id'],))
    db.commit()

    process_donation(35, 'impact-points')
    send_sms('', 'Your ShareCircle match is complete.')
    link = url_for('main.match_view', match_id=match_id)
    create_notification(match['need_user_id'], 'match_completed', 'Your ShareCircle service is complete. You earned 15 Impact Points.', link)
    create_notification(match['offer_user_id'], 'match_completed', 'Your ShareCircle service is complete. You earned 20 Impact Points.', link)
    return jsonify({'status': 'completed', 'awarded_points': {'need_owner': 15, 'offerer': 20}})


@api_bp.post('/matches/<int:match_id>/cancel')
@api_login_required
def cancel_match(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['status'] not in ('accepted', 'arrived'):
        return jsonify({'error': 'Only accepted or arrived matches can be cancelled.'}), 409

    db = get_db()
    cursor = db.execute(
        "UPDATE matches SET status = 'cancelled' WHERE id = ? AND status IN ('accepted', 'arrived')",
        (match_id,),
    )
    if cursor.rowcount != 1:
        db.rollback()
        return jsonify({'error': 'This match can no longer be cancelled.'}), 409

    db.execute('''
        UPDATE needs
        SET status = 'open'
        WHERE id = ? AND status = 'matched'
          AND NOT EXISTS (SELECT 1 FROM matches WHERE need_id = ? AND status <> 'cancelled')
    ''', (match['need_id'], match['need_id']))
    db.execute('''
        UPDATE offers
        SET status = 'available'
        WHERE id = ? AND status = 'matched'
          AND NOT EXISTS (SELECT 1 FROM matches WHERE offer_id = ? AND status <> 'cancelled')
    ''', (match['offer_id'], match['offer_id']))
    db.commit()

    other_id = match['offer_user_id'] if g.user['id'] == match['need_user_id'] else match['need_user_id']
    actor = 'need owner' if g.user['id'] == match['need_user_id'] else 'helper'
    message = f'The {actor} cancelled the match for “{match["need_title"]}”. The need and offer are available again.'
    create_notification(other_id, 'match_cancelled', message, url_for('main.dashboard'))
    create_notification(g.user['id'], 'match_cancelled', 'Match cancelled. The need and offer are available again.', url_for('main.dashboard'))
    return jsonify({'status': 'cancelled', 'released': True})


@api_bp.post('/matches/<int:match_id>/resend-otp')
@api_login_required
def resend_otp(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['need_user_id'] != g.user['id']:
        return jsonify({'error': 'Only the need owner can regenerate the OTP.'}), 403
    if match['status'] != 'paid':
        return jsonify({'error': 'A new OTP can be generated after payment.'}), 409
    otp = _generate_otp()
    db = get_db()
    db.execute('UPDATE matches SET otp = ?, otp_attempts = 0 WHERE id = ?', (otp, match_id))
    db.commit()
    create_notification(
        match['offer_user_id'],
        'match_otp_reset',
        'The need owner regenerated the verification OTP. Ask them for the new code.',
        url_for('main.match_view', match_id=match_id),
    )
    create_notification(
        match['need_user_id'],
        'match_otp_reset',
        'A new verification OTP has been generated for this match.',
        url_for('main.match_view', match_id=match_id),
    )
    return jsonify({'status': 'paid', 'regenerated': True})


@api_bp.get('/matches/<int:match_id>/messages')
@api_login_required
def list_messages(match_id):
    if _get_match_for_user(match_id) is None:
        return jsonify({'error': 'Match not found.'}), 404
    rows = get_db().execute('''
        SELECT m.id, m.body, m.created_at, m.sender_id, u.username, u.full_name
        FROM messages m JOIN users u ON u.id = m.sender_id
        WHERE m.match_id = ? ORDER BY m.created_at ASC, m.id ASC
    ''', (match_id,)).fetchall()
    return jsonify({'items': _json_rows(rows)})


@api_bp.post('/matches/<int:match_id>/messages')
@api_login_required
def send_message(match_id):
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    body = str((request.get_json(silent=True) or {}).get('body', '')).strip()
    if not body:
        return jsonify({'error': 'Message cannot be empty.'}), 400
    if len(body) > 1000:
        return jsonify({'error': 'Message is too long.'}), 400
    db = get_db()
    cursor = db.execute(
        'INSERT INTO messages (match_id, sender_id, body) VALUES (?, ?, ?)',
        (match_id, g.user['id'], body),
    )
    db.commit()
    other_id = match['offer_user_id'] if g.user['id'] == match['need_user_id'] else match['need_user_id']
    create_notification(
        other_id,
        'message_received',
        f'New message from {g.user["full_name"]}.',
        url_for('main.match_view', match_id=match_id),
    )
    send_sms('', body)
    row = db.execute('''
        SELECT m.id, m.body, m.created_at, m.sender_id, u.username, u.full_name
        FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.id = ?
    ''', (cursor.lastrowid,)).fetchone()
    return jsonify({'item': dict(row)}), 201


@api_bp.post('/matches/<int:match_id>/messages/seen')
@api_login_required
def mark_messages_seen(match_id):
    if _get_match_for_user(match_id) is None:
        return jsonify({'error': 'Match not found.'}), 404
    db = get_db()
    db.execute('UPDATE users SET messages_seen_at = CURRENT_TIMESTAMP WHERE id = ?', (g.user['id'],))
    db.commit()
    return jsonify({'ok': True})


@api_bp.post('/ratings')
@api_login_required
def create_rating():
    payload = request.get_json(silent=True) or {}
    match_id = payload.get('match_id')
    stars = payload.get('stars')
    comment = str(payload.get('comment', '')).strip()
    match = _get_match_for_user(match_id)
    if match is None:
        return jsonify({'error': 'Match not found.'}), 404
    if match['status'] != 'completed':
        return jsonify({'error': 'Ratings are available after completion.'}), 409
    try:
        stars = int(stars)
    except (TypeError, ValueError):
        return jsonify({'error': 'Stars must be an integer from 1 to 5.'}), 400
    if stars < 1 or stars > 5:
        return jsonify({'error': 'Stars must be between 1 and 5.'}), 400
    other_id = match['offer_user_id'] if g.user['id'] == match['need_user_id'] else match['need_user_id']
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO ratings (match_id, rater_id, ratee_id, stars, comment) VALUES (?, ?, ?, ?, ?)',
            (match_id, g.user['id'], other_id, stars, comment),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        db.rollback()
        if 'UNIQUE constraint failed' in str(exc):
            return jsonify({'error': 'You already rated this user for this match.'}), 409
        raise
    create_notification(
        other_id,
        'rating_received',
        f'{g.user["full_name"]} rated you {stars}/5.',
        url_for('main.profile', username=g.user['username']),
    )
    return jsonify({'id': cursor.lastrowid}), 201


@api_bp.get('/users/<username>')
def public_user(username):
    db = get_db()
    user = db.execute(
        'SELECT id, username, full_name, location, impact_points, created_at FROM users WHERE username = ?',
        (username,),
    ).fetchone()
    if user is None:
        return jsonify({'error': 'User not found.'}), 404
    rating = db.execute(
        'SELECT COALESCE(AVG(stars), 0) AS avg_rating, COUNT(*) AS count FROM ratings WHERE ratee_id = ?',
        (user['id'],),
    ).fetchone()
    helps_given = db.execute(
        "SELECT COUNT(*) FROM matches m JOIN offers o ON o.id = m.offer_id WHERE m.status = 'completed' AND o.user_id = ?",
        (user['id'],),
    ).fetchone()[0]
    helps_received = db.execute(
        "SELECT COUNT(*) FROM matches m JOIN needs n ON n.id = m.need_id WHERE m.status = 'completed' AND n.user_id = ?",
        (user['id'],),
    ).fetchone()[0]
    needs = db.execute(
        'SELECT id, title, description, category, urgency, status, created_at FROM needs WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user['id'],),
    ).fetchall()
    offers = db.execute(
        'SELECT id, title, description, category, availability, status, created_at FROM offers WHERE user_id = ? ORDER BY created_at DESC LIMIT 5',
        (user['id'],),
    ).fetchall()
    return jsonify({
        'username': user['username'],
        'full_name': user['full_name'],
        'location': user['location'],
        'joined': str(user['created_at'])[:10],
        'impact_points': user['impact_points'],
        'avg_rating': round(float(rating['avg_rating'] or 0), 1),
        'rating_count': int(rating['count']),
        'helps_given': helps_given,
        'helps_received': helps_received,
        'recent_needs': _json_rows(needs),
        'recent_offers': _json_rows(offers),
    })


@api_bp.get('/notifications')
@api_login_required
def notifications_api():
    db = get_db()
    rows = db.execute(
        'SELECT id, type, body, link, read, created_at FROM notifications WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 20',
        (g.user['id'],),
    ).fetchall()
    return jsonify({'items': _json_rows(rows), 'unread_count': unread_count(g.user['id'])})


@api_bp.post('/notifications/read')
@api_login_required
def mark_notifications_read():
    db = get_db()
    db.execute('UPDATE notifications SET read = 1 WHERE user_id = ?', (g.user['id'],))
    db.commit()
    return jsonify({'ok': True})
