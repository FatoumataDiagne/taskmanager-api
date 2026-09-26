def test_create_and_list_workspace(client, auth_headers):
    headers, _ = auth_headers('alice')
    r = client.post('/api/v1/workspaces', json={"name": "Mon espace"}, headers=headers)
    assert r.status_code == 201
    assert r.get_json()['name'] == 'Mon espace'

    r = client.get('/api/v1/workspaces', headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_list_workspaces_requires_auth(client):
    r = client.get('/api/v1/workspaces')
    assert r.status_code == 401


def test_non_member_cannot_access_workspace(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    headers_bob, _ = auth_headers('bob')

    r = client.post('/api/v1/workspaces', json={"name": "Espace Alice"}, headers=headers_alice)
    ws_id = r.get_json()['id']

    r = client.get(f'/api/v1/workspaces/{ws_id}', headers=headers_bob)
    assert r.status_code == 403
    assert r.get_json()['error']['code'] == 'FORBIDDEN'


def test_add_member_success(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    _, bob_id = auth_headers('bob')

    r = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers_alice)
    ws_id = r.get_json()['id']

    r = client.post(f'/api/v1/workspaces/{ws_id}/members',
                     json={"user_id": bob_id, "role": "member"}, headers=headers_alice)
    assert r.status_code == 201
    assert r.get_json()['username'] == 'bob'


def test_add_member_conflict_when_already_member(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    _, bob_id = auth_headers('bob')

    r = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers_alice)
    ws_id = r.get_json()['id']

    client.post(f'/api/v1/workspaces/{ws_id}/members',
                json={"user_id": bob_id, "role": "member"}, headers=headers_alice)
    r = client.post(f'/api/v1/workspaces/{ws_id}/members',
                     json={"user_id": bob_id, "role": "member"}, headers=headers_alice)
    assert r.status_code == 409
    assert r.get_json()['error']['code'] == 'ALREADY_MEMBER'


def test_non_owner_cannot_add_member(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    headers_bob, bob_id = auth_headers('bob')
    _, carol_id = auth_headers('carol')

    r = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers_alice)
    ws_id = r.get_json()['id']
    client.post(f'/api/v1/workspaces/{ws_id}/members',
                json={"user_id": bob_id, "role": "member"}, headers=headers_alice)

    r = client.post(f'/api/v1/workspaces/{ws_id}/members',
                     json={"user_id": carol_id, "role": "member"}, headers=headers_bob)
    assert r.status_code == 403


def test_owner_cannot_be_removed(client, auth_headers):
    headers_alice, alice_id = auth_headers('alice')
    r = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers_alice)
    ws_id = r.get_json()['id']

    r = client.delete(f'/api/v1/workspaces/{ws_id}/members/{alice_id}', headers=headers_alice)
    assert r.status_code == 409
    assert r.get_json()['error']['code'] == 'CANNOT_REMOVE_OWNER'


def test_delete_workspace_owner_only(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    headers_bob, bob_id = auth_headers('bob')

    r = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers_alice)
    ws_id = r.get_json()['id']
    client.post(f'/api/v1/workspaces/{ws_id}/members',
                json={"user_id": bob_id, "role": "member"}, headers=headers_alice)

    r = client.delete(f'/api/v1/workspaces/{ws_id}', headers=headers_bob)
    assert r.status_code == 403

    r = client.delete(f'/api/v1/workspaces/{ws_id}', headers=headers_alice)
    assert r.status_code == 204
