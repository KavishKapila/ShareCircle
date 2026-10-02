import re

from werkzeug.security import generate_password_hash

from app.db import get_db
from app.matching import explain_match, find_best_matches, score_match


def create_user(client, username='alice', email='alice@example.com', password='password123', location='Dehradun'):
    return client.post('/auth/signup', data={
        'full_name': 'Alice Example',
        'username': username,
        'email': email,
        'location': location,
        'password': password,
    }, follow_redirects=False)


def login(client, identifier='alice', password='password123', next_path='/dashboard'):
    return client.post('/auth/login', data={'identifier': identifier, 'password': password, 'next': next_path}, follow_redirects=False)


def add_user(app, user_id, full_name='Bob Example', username='bob', email='bob@example.com', lat=None, lng=None):
    with app.app_context():
        db = get_db()
        db.execute('''
            INSERT INTO users (id, full_name, username, email, location, password_hash, messages_seen_at, lat, lng)
            VALUES (?, ?, ?, ?, 'Dehradun', ?, CURRENT_TIMESTAMP, ?, ?)
        ''', (user_id, full_name, username, email, generate_password_hash('password123'), lat, lng))
        db.commit()


def create_need(client, title='Need algebra tutor', category='Education', urgency='medium', lat=30.3165, lng=78.0322):
    return client.post('/api/needs', json={
        'title': title,
        'description': 'Need weekend help with algebra and linear equations.',
        'category': category,
        'urgency': urgency,
        'lat': lat,
        'lng': lng,
    })


def create_offer(client, title='Weekend algebra tutoring', category='Education', lat=30.3168, lng=78.0324):
    return client.post('/api/offers', json={
        'title': title,
        'description': 'I can tutor algebra and exam practice on weekends.',
        'category': category,
        'availability': 'Saturday morning',
        'lat': lat,
        'lng': lng,
    })


def setup_need_and_offer(client, app):
    create_user(client, username='alice', email='alice@example.com')
    add_user(app, 2)
    need_response = create_need(client)
    need_id = need_response.get_json()['item']['id']
    login(client, 'bob')
    offer_response = create_offer(client)
    offer_id = offer_response.get_json()['item']['id']
    return need_id, offer_id


def switch_to(client, identifier):
    login(client, identifier)


def accept_match(client, need_id):
    return client.post('/api/matches', json={'need_id': need_id})


def test_signup_creates_user(client, app):
    response = create_user(client)
    assert response.status_code == 302
    with app.app_context():
        row = get_db().execute('SELECT username, password_hash, lat, lng FROM users WHERE username = ?', ('alice',)).fetchone()
        assert row['username'] == 'alice'
        assert row['password_hash'] != 'password123'
        assert row['lat'] is None and row['lng'] is None


def test_signup_rejects_duplicate_username(client):
    create_user(client)
    response = create_user(client, username='alice', email='other@example.com')
    assert response.status_code == 200
    assert b'already registered' in response.data


def test_signup_rejects_short_password(client):
    response = create_user(client, password='12345')
    assert response.status_code == 200
    assert b'at least 6 characters' in response.data


def test_login_with_correct_credentials_works(client):
    create_user(client)
    response = login(client)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/dashboard')


def test_login_with_wrong_password_fails(client):
    create_user(client)
    response = login(client, password='wrongpass')
    assert response.status_code == 200
    assert b'Invalid username/email or password' in response.data


def test_login_required_route_redirects(client):
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_api_route_returns_401_json(client):
    response = client.post('/api/needs', json={})
    assert response.status_code == 401
    assert response.get_json()['error']


def test_need_creation_works(client):
    create_user(client)
    response = create_need(client)
    assert response.status_code == 201
    assert response.get_json()['item']['title'] == 'Need algebra tutor'


def test_need_creation_rejects_missing_fields(client):
    create_user(client)
    response = client.post('/api/needs', json={})
    assert response.status_code == 400
    assert response.get_json()['fields']


def test_offer_creation_works(client):
    create_user(client)
    response = create_offer(client)
    assert response.status_code == 201
    assert response.get_json()['item']['category'] == 'Education'


def test_matching_engine_orders_by_score_correctly():
    need = {'category': 'Education', 'title': 'Algebra tutor', 'description': 'Need algebra tutor for weekend exam practice', 'urgency': 'high'}
    offers = [
        {'category': 'Food', 'title': 'Meals', 'description': 'I cook lunches', 'average_rating': 5, 'created_at': '2026-09-01'},
        {'category': 'Education', 'title': 'Weekend algebra tutor', 'description': 'I tutor algebra exam practice', 'average_rating': 4, 'created_at': '2026-09-02'},
    ]
    results = find_best_matches(need, offers)
    assert results[0]['title'] == 'Weekend algebra tutor'
    assert score_match(need, results[0]) > score_match(need, results[1])


def test_matching_engine_caps_at_100():
    need = {'category': 'Education', 'title': 'algebra tutor weekend', 'description': 'algebra tutor weekend exam practice', 'urgency': 'high'}
    offer = dict(need, average_rating=5, created_at='2026-09-01')
    assert score_match(need, offer) == 100.0


def test_matching_engine_gives_same_category_bonus():
    need = {'category': 'Education', 'title': 'Tutor', 'description': 'algebra', 'urgency': 'low'}
    same = {'category': 'education', 'title': 'Cook', 'description': 'food'}
    diff = {'category': 'Food', 'title': 'Cook', 'description': 'food'}
    assert score_match(need, same) - score_match(need, diff) >= 50


def test_accept_creates_match_with_otp_and_marks_items(client, app):
    need_id, offer_id = setup_need_and_offer(client, app)
    response = accept_match(client, need_id)
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'accepted'
    with app.app_context():
        db = get_db()
        match = db.execute('SELECT * FROM matches WHERE id = ?', (data['id'],)).fetchone()
        assert match['status'] == 'accepted'
        assert re.fullmatch(r'\d{6}', match['otp'])
        assert match['otp_attempts'] == 0
        assert db.execute('SELECT status FROM needs WHERE id = ?', (need_id,)).fetchone()['status'] == 'matched'
        assert db.execute('SELECT status FROM offers WHERE id = ?', (offer_id,)).fetchone()['status'] == 'matched'
        notification = db.execute("SELECT body FROM notifications WHERE user_id = 1 AND type = 'match_created' ORDER BY id DESC LIMIT 1").fetchone()
        assert 'OTP' in notification['body']
        assert match['otp'] not in notification['body']


def test_accept_requires_matching_offer_category(client, app):
    create_user(client, username='alice', email='alice@example.com')
    add_user(app, 2)
    create_need(client, category='Education')
    login(client, 'bob')
    create_offer(client, category='Food')
    response = accept_match(client, 1)
    assert response.status_code == 409
    assert 'Education offer' in response.get_json()['error']


def test_arrive_updates_status(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    created = accept_match(client, need_id)
    match_id = created.get_json()['id']
    response = client.post(f'/api/matches/{match_id}/arrive')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'arrived'
    with app.app_context():
        match = get_db().execute('SELECT status, arrived_at FROM matches WHERE id = ?', (match_id,)).fetchone()
        assert match['status'] == 'arrived'
        assert match['arrived_at'] is not None


def test_pay_updates_status_and_amount(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    response = client.post(f'/api/matches/{match_id}/pay', json={'amount': 175.50})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'paid'
    with app.app_context():
        match = get_db().execute('SELECT status, amount_paid, paid_at FROM matches WHERE id = ?', (match_id,)).fetchone()
        assert match['status'] == 'paid'
        assert match['amount_paid'] == 175.50
        assert match['paid_at'] is not None


def test_get_match_hides_otp_from_offer_user_and_reveals_for_need_owner(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 120})
    owner_response = client.get(f'/api/matches/{match_id}')
    assert owner_response.status_code == 200
    owner_match = owner_response.get_json()['match']
    assert re.fullmatch(r'\d{6}', owner_match['otp'])
    otp = owner_match['otp']
    switch_to(client, 'bob')
    offerer_response = client.get(f'/api/matches/{match_id}')
    assert offerer_response.status_code == 200
    assert offerer_response.get_json()['match']['otp'] is None
    assert offerer_response.get_json()['match']['status'] == 'paid'
    assert otp != ''


def test_complete_with_correct_otp_works_and_awards_15_and_20(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 200})
    otp = client.get(f'/api/matches/{match_id}').get_json()['match']['otp']
    switch_to(client, 'bob')
    response = client.post(f'/api/matches/{match_id}/complete', json={'otp': otp})
    assert response.status_code == 200
    assert response.get_json()['status'] == 'completed'
    with app.app_context():
        db = get_db()
        match = db.execute('SELECT status, completed_at FROM matches WHERE id = ?', (match_id,)).fetchone()
        assert match['status'] == 'completed'
        assert match['completed_at'] is not None
        assert db.execute('SELECT status FROM needs WHERE id = ?', (need_id,)).fetchone()['status'] == 'fulfilled'
        assert db.execute('SELECT impact_points FROM users WHERE id = 1').fetchone()['impact_points'] == 15
        assert db.execute('SELECT impact_points FROM users WHERE id = 2').fetchone()['impact_points'] == 20


def test_complete_with_wrong_otp_fails_after_three_attempts(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 250})
    switch_to(client, 'bob')
    for attempt in range(3):
        response = client.post(f'/api/matches/{match_id}/complete', json={'otp': '000000'})
        assert response.status_code == 400
        assert response.get_json()['error'] == 'Incorrect OTP'
        assert response.get_json()['attempts_remaining'] == max(0, 2 - attempt)
    locked = client.post(f'/api/matches/{match_id}/complete', json={'otp': '000000'})
    assert locked.status_code == 409
    assert 'locked' in locked.get_json()['error'].lower()
    with app.app_context():
        assert get_db().execute('SELECT otp_attempts FROM matches WHERE id = ?', (match_id,)).fetchone()['otp_attempts'] == 3


def test_resend_otp_resets_attempts(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 300})
    switch_to(client, 'bob')
    client.post(f'/api/matches/{match_id}/complete', json={'otp': '000000'})
    client.post(f'/api/matches/{match_id}/complete', json={'otp': '000000'})
    client.post(f'/api/matches/{match_id}/complete', json={'otp': '000000'})
    switch_to(client, 'alice')
    response = client.post(f'/api/matches/{match_id}/resend-otp')
    assert response.status_code == 200
    with app.app_context():
        match = get_db().execute('SELECT otp, otp_attempts, status FROM matches WHERE id = ?', (match_id,)).fetchone()
        assert match['status'] == 'paid'
        assert match['otp_attempts'] == 0
        assert re.fullmatch(r'\d{6}', match['otp'])


def test_active_match_endpoint_returns_current_match(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    response = client.get('/api/matches/active')
    assert response.status_code == 200
    assert response.get_json()['match']['id'] == match_id
    assert response.get_json()['match']['status'] == 'accepted'


def test_nearby_endpoint_filters_by_offer_categories_and_distance(client, app):
    create_user(client, username='alice', email='alice@example.com')
    add_user(app, 2, lat=30.3165, lng=78.0322)
    create_need(client, title='Education near', category='Education', lat=30.3170, lng=78.0325)
    create_need(client, title='Food near', category='Food', lat=30.3170, lng=78.0325)
    login(client, 'bob')
    create_offer(client, category='Education', lat=30.3165, lng=78.0322)
    response = client.get('/api/needs/nearby?lat=30.3165&lng=78.0322&radius_km=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['categories'] == ['Education']
    assert len(data['items']) == 1
    assert data['items'][0]['title'] == 'Education near'
    assert data['items'][0]['distance_km'] >= 0


def test_nearby_endpoint_respects_radius(client, app):
    create_user(client, username='alice', email='alice@example.com')
    add_user(app, 2)
    create_need(client, category='Education', lat=30.3165, lng=78.0322)
    login(client, 'bob')
    create_offer(client, category='Education')
    response = client.get('/api/needs/nearby?lat=30.3165&lng=78.0322&radius_km=0.5')
    assert response.status_code == 200
    assert len(response.get_json()['items']) == 1


def test_location_endpoint_updates_last_known_location(client, app):
    create_user(client)
    response = client.post('/api/location', json={'lat': 30.32, 'lng': 78.04})
    assert response.status_code == 200
    with app.app_context():
        row = get_db().execute('SELECT lat, lng, last_location_at FROM users WHERE id = 1').fetchone()
        assert row['lat'] == 30.32
        assert row['lng'] == 78.04
        assert row['last_location_at'] is not None


def test_login_with_available_offer_opens_nearby(client):
    create_user(client)
    create_offer(client)
    client.post('/auth/logout')
    response = login(client, 'alice')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/nearby')


def test_nearby_page_requires_login(client):
    response = client.get('/nearby')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_match_page_requires_login(client):
    response = client.get('/match/999')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_match_page_renders_for_participant(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    response = client.get(f'/match/{match_id}')
    assert response.status_code == 200
    assert b'Open in Google Maps' in response.data or b'Navigate to the need' in response.data


def test_rating_creation_works_and_is_unique(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 100})
    otp = client.get(f'/api/matches/{match_id}').get_json()['match']['otp']
    switch_to(client, 'bob')
    client.post(f'/api/matches/{match_id}/complete', json={'otp': otp})
    response = client.post('/api/ratings', json={'match_id': match_id, 'stars': 5, 'comment': 'Excellent'})
    assert response.status_code == 201
    duplicate = client.post('/api/ratings', json={'match_id': match_id, 'stars': 4, 'comment': 'Again'})
    assert duplicate.status_code == 409


def test_message_creation_works(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    response = client.post(f'/api/matches/{match_id}/messages', json={'body': 'Hello, are you free Saturday?'})
    assert response.status_code == 201
    assert response.get_json()['item']['body'].startswith('Hello')


def test_explain_match_returns_correct_breakdown():
    need = {'category': 'Education', 'title': 'algebra tutor weekend', 'description': 'Need exam practice', 'urgency': 'high'}
    offer = {'category': 'Education', 'title': 'weekend tutor', 'description': 'algebra exam practice', 'average_rating': 4}
    breakdown = explain_match(need, offer)
    assert breakdown['category'] == 50
    assert breakdown['urgency'] == 10
    assert breakdown['reputation'] == 8.0
    assert breakdown['total'] == score_match(need, offer)
    assert 'algebra' in breakdown['shared_keywords']


def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json() == {'status': 'ok', 'db': 'ok', 'version': '1.0'}


def test_public_profile_json(client, app):
    create_user(client)
    with app.app_context():
        username = get_db().execute('SELECT username FROM users WHERE id=1').fetchone()['username']
    response = client.get(f'/api/users/{username}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == username
    assert set(['avg_rating', 'rating_count', 'helps_given', 'helps_received']).issubset(data)


def test_static_and_404_routes(client):
    assert client.get('/').status_code == 200
    assert client.get('/definitely-not-a-page').status_code == 404


def test_embedded_map_page_is_removed(client):
    response = client.get('/map')
    assert response.status_code == 404


def test_impact_page_shows_supply_demand_ratio_for_open_needs_and_available_offers(client, app):
    create_user(client, username='alice', email='alice@example.com')
    add_user(app, 2)
    create_need(client, title='Education need 1', category='Education')
    create_need(client, title='Education need 2', category='Education')
    create_need(client, title='Food need', category='Food')
    login(client, 'bob')
    create_offer(client, category='Education')
    response = client.get('/impact')
    assert response.status_code == 200
    assert b'data-ratio="0.5"' in response.data
    assert b'0.50' in response.data
    assert b'1 more helper needed' in response.data
    assert b'data-ratio="0.0"' in response.data


def test_completed_match_has_printable_receipt_for_participants_only(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 225})
    otp = client.get(f'/api/matches/{match_id}').get_json()['match']['otp']
    switch_to(client, 'bob')
    client.post(f'/api/matches/{match_id}/complete', json={'otp': otp})

    response = client.get(f'/match/{match_id}/receipt')
    assert response.status_code == 200
    assert b'Impact Receipt' in response.data
    assert b'225.00' in response.data
    assert b'@media print' not in response.data  # print CSS lives in the shared stylesheet

    add_user(app, 3, full_name='Cara Example', username='cara', email='cara@example.com')
    login(client, 'cara')
    forbidden = client.get(f'/match/{match_id}/receipt')
    assert forbidden.status_code == 404


def test_base_page_exposes_hindi_toggle(client):
    response = client.get('/impact')
    assert response.status_code == 200
    assert b'data-language-toggle' in response.data
    assert b'data-i18n="impact.title"' in response.data


def test_cancel_match_releases_need_and_offer(client, app):
    need_id, offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    response = client.post(f'/api/matches/{match_id}/cancel')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'cancelled'
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT status FROM matches WHERE id = ?', (match_id,)).fetchone()['status'] == 'cancelled'
        assert db.execute('SELECT status FROM needs WHERE id = ?', (need_id,)).fetchone()['status'] == 'open'
        assert db.execute('SELECT status FROM offers WHERE id = ?', (offer_id,)).fetchone()['status'] == 'available'


def test_cancel_paid_match_is_rejected(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 100})
    response = client.post(f'/api/matches/{match_id}/cancel')
    assert response.status_code == 409


def test_public_receipt_verification_is_signed_and_privacy_aware(client, app):
    need_id, _offer_id = setup_need_and_offer(client, app)
    match_id = accept_match(client, need_id).get_json()['id']
    client.post(f'/api/matches/{match_id}/arrive')
    switch_to(client, 'alice')
    client.post(f'/api/matches/{match_id}/pay', json={'amount': 125})
    otp = client.get(f'/api/matches/{match_id}').get_json()['match']['otp']
    switch_to(client, 'bob')
    client.post(f'/api/matches/{match_id}/complete', json={'otp': otp})
    owner_response = client.get(f'/match/{match_id}/receipt')
    assert owner_response.status_code == 200
    import re as _re
    match = _re.search(rb'href="([^"]*impact/verify/SC-[^"]*)"', owner_response.data)
    assert match
    verify_url = match.group(1).decode('utf-8').replace('&amp;', '&')
    verify_response = client.get(verify_url)
    assert verify_response.status_code == 200
    assert b'Verified Impact Receipt' in verify_response.data
    assert b'125.00' not in verify_response.data
    assert client.get(verify_url + 'x').status_code == 404


def test_reset_data_requires_password_and_confirmation(client, app):
    create_user(client)
    bad = client.post('/reset-data', data={'password': 'wrong', 'confirmation': 'RESET ALL DATA'})
    assert bad.status_code == 403
    good = client.post('/reset-data', data={'password': 'ShareCircle123', 'confirmation': 'RESET ALL DATA'})
    assert good.status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
        assert get_db().execute('SELECT COUNT(*) FROM needs').fetchone()[0] == 0



def test_signup_rejects_email_without_dotted_domain(client):
    response = create_user(client, username='kavish', email='kavish@gmail')
    assert response.status_code == 200
    assert b'valid email address' in response.data


def test_signup_accepts_common_and_institutional_email_formats(client):
    formats = ['kavish@gmail.com', 'user.name+tag@outlook.com', 'hello@yahoo.co.uk', 'person@icloud.com', 'student@university.edu', 'student@college.ac.in', 'person@business.co.in']
    for index, email in enumerate(formats, start=10):
        response = create_user(client, username=f'user{index}', email=email)
        assert response.status_code == 302
        client.post('/auth/logout')


def test_manual_location_can_be_saved_and_used_for_nearby_matching(client, app):
    create_user(client, location='Rajpur Road, Dehradun')
    create_offer(client, category='Education', lat=None, lng=None)
    add_user(app, 2, username='bob', email='bob@example.com')
    with app.app_context():
        db = get_db()
        db.execute('UPDATE users SET location = ? WHERE username = ?', ('Rajpur Road, Dehradun', 'bob'))
        db.execute("INSERT INTO needs (user_id, title, description, category, urgency, status, lat, lng) VALUES (2, 'Need a tutor', 'Math help', 'Education', 'high', 'open', NULL, NULL)")
        db.commit()
    save = client.post('/api/location/manual', json={'location': 'Rajpur Road, Dehradun'})
    assert save.status_code == 200
    response = client.get('/api/needs/nearby?location=Rajpur%20Road')
    assert response.status_code == 200
    data = response.get_json()
    assert data['location_mode'] == 'manual'
    assert data['items'][0]['title'] == 'Need a tutor'
    assert data['items'][0]['distance_km'] is None
