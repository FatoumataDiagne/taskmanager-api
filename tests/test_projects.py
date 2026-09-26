def _make_workspace(client, headers, name="Espace"):
    r = client.post('/api/v1/workspaces', json={"name": name}, headers=headers)
    return r.get_json()['id']


def test_create_and_list_projects(client, auth_headers):
    headers, _ = auth_headers('alice')
    ws_id = _make_workspace(client, headers)

    r = client.post(f'/api/v1/workspaces/{ws_id}/projects', json={"name": "Site web"}, headers=headers)
    assert r.status_code == 201
    assert r.get_json()['status'] == 'active'

    r = client.get(f'/api/v1/workspaces/{ws_id}/projects', headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_non_member_cannot_see_project(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    headers_bob, _ = auth_headers('bob')
    ws_id = _make_workspace(client, headers_alice)
    pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                       json={"name": "Site web"}, headers=headers_alice).get_json()['id']

    r = client.get(f'/api/v1/projects/{pid}', headers=headers_bob)
    assert r.status_code == 403


def test_archive_project(client, auth_headers):
    headers, _ = auth_headers('alice')
    ws_id = _make_workspace(client, headers)
    pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                       json={"name": "Site web"}, headers=headers).get_json()['id']

    r = client.patch(f'/api/v1/projects/{pid}', json={"status": "archived"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()['status'] == 'archived'


def test_delete_project(client, auth_headers):
    headers, _ = auth_headers('alice')
    ws_id = _make_workspace(client, headers)
    pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                       json={"name": "Site web"}, headers=headers).get_json()['id']

    r = client.delete(f'/api/v1/projects/{pid}', headers=headers)
    assert r.status_code == 204

    r = client.get(f'/api/v1/projects/{pid}', headers=headers)
    assert r.status_code == 404