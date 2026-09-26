import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app('test')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Crée un utilisateur et retourne (headers, user_id) prêts à l'emploi."""
    def _make(username='alice', email=None, password='pass1234'):
        email = email or f'{username}@test.com'
        r = client.post('/api/v1/auth/register', json={
            "username": username, "email": email, "password": password
        })
        user_id = r.get_json()['id']
        r = client.post('/api/v1/auth/login', json={
            "username": username, "password": password
        })
        token = r.get_json()['access_token']
        return {"Authorization": f"Bearer {token}"}, user_id
    return _make
