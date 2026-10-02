from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
import re
from werkzeug.security import check_password_hash, generate_password_hash
from ..auth import login_required
from ..db import get_db
from ..integrations import geocode, send_email

auth_bp = Blueprint('auth', __name__)


EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def _valid_email(email):
    """Validate normal email/domain syntax without restricting providers."""
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        return False
    local, domain = email.rsplit('@', 1)
    if len(local) > 64 or '..' in local or '..' in domain:
        return False
    tld = domain.rsplit('.', 1)[-1]
    return len(tld) >= 2 and (tld.isalpha() or tld.lower().startswith('xn--'))


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
        return
    g.user = get_db().execute(
        '''SELECT id, full_name, username, email, location, impact_points, is_hackathon,
                  messages_seen_at, lat, lng, last_location_at, created_at
           FROM users WHERE id = ?''',
        (user_id,),
    ).fetchone()
    if g.user is None:
        session.clear()


def _safe_next():
    target = request.args.get('next') or request.form.get('next')
    if target and target.startswith('/') and not target.startswith('//'):
        return target
    return url_for('main.dashboard')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        location = request.form.get('location', '').strip()
        password = request.form.get('password', '')
        errors = []
        field_errors = {}
        if len(full_name) < 2:
            field_errors['full_name'] = 'Enter your full name.'
            errors.append('Enter your full name.')
        if len(username) < 3:
            message = 'Username must be at least 3 characters.'
            errors.append(message); field_errors['username'] = message
        if not _valid_email(email):
            message = 'Enter a valid email address, such as kavish@gmail.com or name@university.ac.in.'
            errors.append(message); field_errors['email'] = message
        if len(location) < 2:
            message = 'Enter your neighborhood or city.'
            errors.append(message); field_errors['location'] = message
        if len(password) < 6:
            message = 'Password must be at least 6 characters.'
            errors.append(message); field_errors['password'] = message
        db = get_db()
        existing = db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email),
        ).fetchone()
        if existing:
            message = 'That username or email is already registered.'
            errors.append(message)
            if existing['id']:
                field_errors['username'] = message
                field_errors['email'] = message
        if errors:
            for message in errors:
                flash(message, 'error')
            return render_template('auth/signup.html', field_errors=field_errors)
        cursor = db.execute(
            '''INSERT INTO users
               (full_name, username, email, location, password_hash, messages_seen_at,
                lat, lng, last_location_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, NULL, NULL, NULL)''',
            (full_name, username, email, location, generate_password_hash(password)),
        )
        db.commit()
        session.clear()
        session['user_id'] = cursor.lastrowid
        send_email(email, 'Welcome to ShareCircle', f'Welcome, {full_name}!')
        geocode(location)
        flash('Account created. Welcome to ShareCircle!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('auth/signup.html')


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not _valid_email(email):
            flash('Enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        # Recovery delivery is intentionally non-enumerating. The current local
        # build does not expose password-reset tokens, so never reveal whether an
        # address exists; provide a clear next step instead.
        flash('If that email belongs to a ShareCircle account, recovery instructions can be sent when email recovery is configured.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        user = get_db().execute(
            'SELECT * FROM users WHERE username = ? OR email = ?',
            (identifier, identifier.lower()),
        ).fetchone()
        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid username/email or password.', 'error')
            return render_template('auth/login.html', field_errors={'identifier': 'Check your username/email and password.'})
        session.clear()
        session['user_id'] = user['id']
        session.permanent = request.form.get('remember') == '1'
        explicit_next = request.args.get('next') or request.form.get('next')
        if not explicit_next:
            has_offer = get_db().execute(
                "SELECT id FROM offers WHERE user_id = ? AND status IN ('available', 'matched') LIMIT 1",
                (user['id'],),
            ).fetchone()
            if has_offer:
                return redirect(url_for('main.nearby'))
        return redirect(_safe_next())
    return render_template('auth/login.html')


@auth_bp.post('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))
