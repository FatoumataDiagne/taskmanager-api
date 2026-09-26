def test_register_success(client):
    r = client.post('/api/v1/auth/register', json={
        "username": "alice", "email": "alice@test.com", "password": "pass1234"
    })
    assert r.status_code == 201
    assert r.get_json()['username'] == 'alice'


def test_register_missing_fields(client):
    r = client.post('/api/v1/auth/register', json={"username": "alice"})
    assert r.status_code == 400
    assert r.get_json()['error']['code'] == 'MISSING_FIELDS'


def test_register_duplicate_username(client, auth_headers):
    auth_headers('alice')
    r = client.post('/api/v1/auth/register', json={
        "username": "alice", "email": "autre@test.com", "password": "pass1234"
    })
    assert r.status_code == 400
    assert r.get_json()['error']['code'] == 'REGISTER_CONFLICT'


def test_login_success(client):
    client.post('/api/v1/auth/register', json={
        "username": "alice", "email": "alice@test.com", "password": "pass1234"
    })
    r = client.post('/api/v1/auth/login', json={"username": "alice", "password": "pass1234"})
    assert r.status_code == 200
    body = r.get_json()
    assert 'access_token' in body and 'refresh_token' in body


def test_login_invalid_credentials(client):
    r = client.post('/api/v1/auth/login', json={"username": "inconnu", "password": "x"})
    assert r.status_code == 401
    assert r.get_json()['error']['code'] == 'INVALID_CREDENTIALS'


def test_me_requires_token(client):
    r = client.get('/api/v1/auth/me')
    assert r.status_code == 401


def test_me_with_token(client, auth_headers):
    headers, user_id = auth_headers('alice')
    r = client.get('/api/v1/auth/me', headers=headers)
    assert r.status_code == 200
    assert r.get_json()['id'] == user_id
