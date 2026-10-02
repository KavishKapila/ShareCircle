from flask import Blueprint, jsonify, request

from ..db import get_db
from .api import _bearing_deg, _generate_otp, _haversine_km

judge_bp = Blueprint('judge', __name__)

# Judge Mode is a presentation-only demo. It MUST NOT create rows in the
# production SQLite database. State lives only in this Python process and is
# discarded when the demo ends/restarts.
_DEMO_RUNS = {}
# Judge demo IDs must be positive because Flask's built-in <int:...> route
# converter does not match negative numbers. These IDs are process-local only
# and are never written to the database.
_NEXT_DEMO_ID = 1000000

DEMO_OWNER = {
    'username': 'judge_owner',
    'full_name': 'Priya Sharma',
    'email': 'judge.owner@sharecircle.demo',
    'location': 'Rajpur Road, Dehradun',
    'lat': 30.3165,
    'lng': 78.0322,
}
DEMO_HELPER = {
    'username': 'judge_helper',
    'full_name': 'Arjun Verma',
    'email': 'judge.helper@sharecircle.demo',
    'location': 'Clement Town, Dehradun',
    'lat': 30.3016,
    'lng': 78.0142,
}
DEMO_NEED = {
    'title': 'Pick up my prescription from the pharmacy',
    'description': (
        "Recovering from a minor knee surgery and can't drive yet. Need someone to collect "
        'medicines from Apex Pharmacy on Rajpur Road before evening.'
    ),
    'category': 'Health',
    'urgency': 'high',
}
DEMO_OFFER = {
    'title': 'Free most afternoons for local errands',
    'description': 'Happy to help with pharmacy runs, small pickups, and quick local errands around Dehradun.',
    'category': 'Health',
    'availability': 'Weekday afternoons',
}
DEMO_AMOUNT = 120.0

STEP_NARRATION = {
    'accepted': "Arjun spots Priya's need on the Nearby feed and accepts it. ShareCircle generates a one-time code for the real-world handoff.",
    'arrived': 'Arjun reaches Rajpur Road and marks himself as arrived.',
    'paid': 'Priya hands Arjun ₹120 in person and records the payment in the app.',
    'completed': 'Priya reads the OTP out loud, Arjun enters it, and ShareCircle confirms the help really happened — not just a "mark as done" button.',
    'rated': 'Both neighbors rate the experience 5★, closing the loop and posting Impact Points to their profiles.',
}


def purge_legacy_demo_data(db):
    """Remove demo rows left by older Judge Mode versions.

    This is intentionally defensive: old builds inserted judge_owner and
    judge_helper into the real database. Cascading foreign keys remove their
    old needs/offers/matches/ratings/messages/notifications as well.
    """
    db.execute(
        'DELETE FROM users WHERE username IN (?, ?)',
        (DEMO_OWNER['username'], DEMO_HELPER['username']),
    )
    db.commit()


def _new_demo_id():
    global _NEXT_DEMO_ID
    demo_id = _NEXT_DEMO_ID
    _NEXT_DEMO_ID += 1
    return demo_id


def _make_run(demo_id):
    otp = _generate_otp()
    return {
        'id': demo_id,
        'status': 'accepted',
        'otp': otp,
        'amount_paid': 0,
        'arrived_at': None,
        'paid_at': None,
        'completed_at': None,
        'rated': False,
        'owner_points': 0,
        'helper_points': 0,
    }


def _snapshot(run):
    distance = round(
        _haversine_km(
            DEMO_HELPER['lat'], DEMO_HELPER['lng'],
            DEMO_OWNER['lat'], DEMO_OWNER['lng'],
        ),
        2,
    )
    bearing = round(
        _bearing_deg(
            DEMO_HELPER['lat'], DEMO_HELPER['lng'],
            DEMO_OWNER['lat'], DEMO_OWNER['lng'],
        ),
        1,
    )
    return {
        'id': run['id'],
        'status': run['status'],
        'otp': run['otp'],
        'amount_paid': run['amount_paid'],
        'distance_km': distance,
        'bearing_deg': bearing,
        'rated': run['rated'],
        'owner': {
            'full_name': DEMO_OWNER['full_name'],
            'username': DEMO_OWNER['username'],
            'impact_points': run['owner_points'],
        },
        'helper': {
            'full_name': DEMO_HELPER['full_name'],
            'username': DEMO_HELPER['username'],
            'impact_points': run['helper_points'],
        },
        'need': {
            'title': DEMO_NEED['title'],
            'description': DEMO_NEED['description'],
            'category': DEMO_NEED['category'],
            'urgency': DEMO_NEED['urgency'],
            'status': 'fulfilled' if run['status'] in ('completed', 'rated') else 'matched',
        },
        'offer': {
            'title': DEMO_OFFER['title'],
            'description': DEMO_OFFER['description'],
            'category': DEMO_OFFER['category'],
            'availability': DEMO_OFFER['availability'],
            'status': 'completed' if run['status'] in ('completed', 'rated') else 'matched',
        },
    }


def _get_run(match_id):
    return _DEMO_RUNS.get(match_id)


@judge_bp.post('/start')
def start():
    # No DB reads/writes are needed to start a Judge Mode demo.
    demo_id = _new_demo_id()
    _DEMO_RUNS[demo_id] = _make_run(demo_id)
    return jsonify({
        'match': _snapshot(_DEMO_RUNS[demo_id]),
        'narration': STEP_NARRATION['accepted'],
    }), 201


@judge_bp.post('/advance/<int:match_id>')
def advance(match_id):
    run = _get_run(match_id)
    if run is None:
        return jsonify({'error': 'Unknown judge-mode match. Start a fresh demo run.'}), 404

    payload = request.get_json(silent=True) or {}
    step = str(payload.get('step', '')).strip()

    if step == 'arrive':
        if run['status'] != 'accepted':
            return jsonify({'error': 'This demo match is not waiting for arrival.'}), 409
        run['status'] = 'arrived'
        run['arrived_at'] = 'demo'
        narration_key = 'arrived'
    elif step == 'pay':
        if run['status'] != 'arrived':
            return jsonify({'error': 'This demo match is not waiting for payment.'}), 409
        run['status'] = 'paid'
        run['amount_paid'] = DEMO_AMOUNT
        run['paid_at'] = 'demo'
        narration_key = 'paid'
    elif step == 'complete':
        if run['status'] != 'paid':
            return jsonify({'error': 'This demo match is not waiting for completion.'}), 409
        run['status'] = 'completed'
        run['completed_at'] = 'demo'
        run['owner_points'] = 15
        run['helper_points'] = 20
        narration_key = 'completed'
    elif step == 'rate':
        if run['status'] != 'completed':
            return jsonify({'error': 'This demo match is not ready to rate.'}), 409
        run['status'] = 'rated'
        run['rated'] = True
        narration_key = 'rated'
    else:
        return jsonify({'error': 'Unknown demo step.'}), 400

    return jsonify({
        'match': _snapshot(run),
        'narration': STEP_NARRATION[narration_key],
    })
import secrets
import time

from flask import Blueprint, current_app, jsonify, request, session
from werkzeug.security import generate_password_hash

from ..db import get_db

hackathon_bp = Blueprint('hackathon', __name__)


def _enabled():
    return bool(current_app.config.get('HACKATHON_UTILITIES_ENABLED', True))


def _guard():
    if not _enabled():
        return jsonify({'error': 'Hackathon Utilities are disabled.'}), 404
    return None


def _account_row(row):
    return {
        'id': row['id'],
        'full_name': row['full_name'],
        'username': row['username'],
        'email': row['email'],
        'location': row['location'],
        'impact_points': int(row['impact_points'] or 0),
        'created_at': row['created_at'],
    }


@hackathon_bp.get('/accounts')
def accounts():
    blocked = _guard()
    if blocked:
        return blocked
    rows = get_db().execute('''
        SELECT id, full_name, username, email, location, impact_points, created_at
        FROM users
        WHERE is_hackathon = 1
        ORDER BY created_at DESC, id DESC
    ''').fetchall()
    return jsonify({'accounts': [_account_row(row) for row in rows]})


@hackathon_bp.post('/accounts')
def create_account():
    blocked = _guard()
    if blocked:
        return blocked

    db = get_db()
    count = db.execute('SELECT COUNT(*) AS c FROM users WHERE is_hackathon = 1').fetchone()['c']
    sequence = int(count) + 1
    nonce = secrets.token_hex(3)
    username = f'hack-{sequence}-{nonce}'
    email = f'{username}@hackathon.sharecircle.local'
    full_name = f'Hackathon Judge {sequence}'
    location = 'Hackathon test circle'

    # The account intentionally has no usable human password. A strong random
    # hash satisfies the existing schema while the dedicated switch endpoint
    # provides the passwordless judge workflow.
    password_hash = generate_password_hash(secrets.token_urlsafe(32))
    cursor = db.execute('''
        INSERT INTO users
            (full_name, username, email, location, password_hash, messages_seen_at,
             lat, lng, last_location_at, is_hackathon)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL, NULL, NULL, 1)
    ''', (full_name, username, email, location, password_hash))
    db.commit()

    user_id = cursor.lastrowid
    session.clear()
    session['user_id'] = user_id
    session.permanent = False

    row = db.execute('''
        SELECT id, full_name, username, email, location, impact_points, created_at
        FROM users WHERE id = ?
    ''', (user_id,)).fetchone()
    return jsonify({'account': _account_row(row)}), 201


@hackathon_bp.post('/accounts/<int:user_id>/switch')
def switch_account(user_id):
    blocked = _guard()
    if blocked:
        return blocked

    row = get_db().execute('''
        SELECT id, full_name, username, email, location, impact_points, created_at
        FROM users WHERE id = ? AND is_hackathon = 1
    ''', (user_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'That quick account no longer exists.'}), 404

    session.clear()
    session['user_id'] = row['id']
    session.permanent = False
    return jsonify({'account': _account_row(row)})


@hackathon_bp.post('/accounts/<int:user_id>/delete')
def delete_account(user_id):
    blocked = _guard()
    if blocked:
        return blocked

    db = get_db()
    row = db.execute('SELECT id FROM users WHERE id = ? AND is_hackathon = 1', (user_id,)).fetchone()
    if row is None:
        return jsonify({'error': 'That quick account no longer exists.'}), 404

    if session.get('user_id') == user_id:
        session.clear()
    db.execute('DELETE FROM users WHERE id = ? AND is_hackathon = 1', (user_id,))
    db.commit()
    return jsonify({'ok': True})


@judge_bp.post('/reset')
def reset():
    """Clear only in-memory Judge Mode runs; never touches the real DB."""
    _DEMO_RUNS.clear()
    return jsonify({'ok': True})
