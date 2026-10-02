import tempfile
from pathlib import Path

import pytest

from app import create_app
from app.db import get_db


@pytest.fixture()
def app():
    with tempfile.TemporaryDirectory() as folder:
        db_path = str(Path(folder) / 'test.db')
        app = create_app({'TESTING': True, 'DATABASE': db_path, 'SECRET_KEY': 'test-secret'})
        with app.app_context():
            get_db().execute('PRAGMA foreign_keys = ON')
        yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, identifier='alice', password='password123'):
    return client.post('/auth/login', data={'identifier': identifier, 'password': password}, follow_redirects=False)


def create_user(client, username='alice', email='alice@example.com', password='password123'):
    return client.post('/auth/signup', data={
        'full_name': 'Alice Example', 'username': username, 'email': email,
        'location': 'Dehradun', 'password': password,
    }, follow_redirects=False)
