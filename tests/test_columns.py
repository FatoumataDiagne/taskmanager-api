def _make_project(client, headers):
    ws_id = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers).get_json()['id']
    pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                       json={"name": "Site"}, headers=headers).get_json()['id']
    return ws_id, pid


def test_create_and_list_columns(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid = _make_project(client, headers)

    r = client.post(f'/api/v1/projects/{pid}/columns', json={"name": "To Do", "order": 0}, headers=headers)
    assert r.status_code == 201

    r = client.get(f'/api/v1/projects/{pid}/columns', headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) == 1


def test_non_member_cannot_manage_columns(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    headers_bob, _ = auth_headers('bob')
    _, pid = _make_project(client, headers_alice)

    r = client.post(f'/api/v1/projects/{pid}/columns', json={"name": "To Do"}, headers=headers_bob)
    assert r.status_code == 403


def test_rename_and_reorder_column(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid = _make_project(client, headers)
    cid = client.post(f'/api/v1/projects/{pid}/columns',
                       json={"name": "To Do"}, headers=headers).get_json()['id']

    r = client.patch(f'/api/v1/columns/{cid}', json={"name": "Backlog", "order": 2}, headers=headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body['name'] == 'Backlog'
    assert body['order'] == 2


def test_delete_column(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid = _make_project(client, headers)
    cid = client.post(f'/api/v1/projects/{pid}/columns',
                       json={"name": "To Do"}, headers=headers).get_json()['id']

    r = client.delete(f'/api/v1/columns/{cid}', headers=headers)
    assert r.status_code == 204

    r = client.get(f'/api/v1/projects/{pid}/columns', headers=headers)
    assert r.get_json() == []