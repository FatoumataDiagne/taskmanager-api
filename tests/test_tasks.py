def _make_column(client, headers):
    ws_id = client.post('/api/v1/workspaces', json={"name": "Espace"}, headers=headers).get_json()['id']
    pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                       json={"name": "Site"}, headers=headers).get_json()['id']
    col_id = client.post(f'/api/v1/projects/{pid}/columns',
                          json={"name": "To Do"}, headers=headers).get_json()['id']
    return ws_id, pid, col_id


def test_create_task(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, _, col_id = _make_column(client, headers)

    r = client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Ecrire les tests"}, headers=headers)
    assert r.status_code == 201
    assert r.get_json()['priority'] == 'medium'  # valeur par défaut


def test_cannot_assign_non_member(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    _, bob_id = auth_headers('bob')
    _, _, col_id = _make_column(client, headers_alice)

    r = client.post(f'/api/v1/columns/{col_id}/tasks',
                     json={"title": "Tâche", "assignee_id": bob_id}, headers=headers_alice)
    assert r.status_code == 409
    assert r.get_json()['error']['code'] == 'NOT_WORKSPACE_MEMBER'


def test_can_assign_member(client, auth_headers):
    headers_alice, _ = auth_headers('alice')
    _, bob_id = auth_headers('bob')
    ws_id, _, col_id = _make_column(client, headers_alice)
    client.post(f'/api/v1/workspaces/{ws_id}/members',
                json={"user_id": bob_id, "role": "member"}, headers=headers_alice)

    r = client.post(f'/api/v1/columns/{col_id}/tasks',
                     json={"title": "Tâche", "assignee_id": bob_id}, headers=headers_alice)
    assert r.status_code == 201
    assert r.get_json()['assignee_id'] == bob_id


def test_move_task_between_columns(client, auth_headers):
    headers, _ = auth_headers('alice')
    ws_id, pid, col1 = _make_column(client, headers)
    col2 = client.post(f'/api/v1/projects/{pid}/columns',
                        json={"name": "Done"}, headers=headers).get_json()['id']
    tid = client.post(f'/api/v1/columns/{col1}/tasks',
                       json={"title": "Tâche"}, headers=headers).get_json()['id']

    r = client.patch(f'/api/v1/tasks/{tid}', json={"column_id": col2}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()['column_id'] == col2


def test_cannot_move_task_to_column_of_another_project(client, auth_headers):
    headers, _ = auth_headers('alice')
    ws_id, pid, col1 = _make_column(client, headers)
    other_pid = client.post(f'/api/v1/workspaces/{ws_id}/projects',
                             json={"name": "Autre projet"}, headers=headers).get_json()['id']
    other_col = client.post(f'/api/v1/projects/{other_pid}/columns',
                             json={"name": "To Do"}, headers=headers).get_json()['id']
    tid = client.post(f'/api/v1/columns/{col1}/tasks',
                       json={"title": "Tâche"}, headers=headers).get_json()['id']

    r = client.patch(f'/api/v1/tasks/{tid}', json={"column_id": other_col}, headers=headers)
    assert r.status_code == 409
    assert r.get_json()['error']['code'] == 'INVALID_COLUMN_TARGET'


def test_filter_tasks_by_priority(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid, col_id = _make_column(client, headers)
    client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Basse", "priority": "low"}, headers=headers)
    client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Haute", "priority": "high"}, headers=headers)

    r = client.get(f'/api/v1/projects/{pid}/tasks?priority=high', headers=headers)
    assert r.status_code == 200
    body = r.get_json()
    titles = [t['title'] for t in body['data']]
    assert titles == ['Haute']
    assert body['meta']['total'] == 1


def test_pagination_on_tasks(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid, col_id = _make_column(client, headers)
    for i in range(5):
        client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": f"Tâche {i}"}, headers=headers)

    r = client.get(f'/api/v1/projects/{pid}/tasks?page=1&per_page=2', headers=headers)
    body = r.get_json()
    assert len(body['data']) == 2
    assert body['meta'] == {"page": 1, "per_page": 2, "total": 5, "total_pages": 3}

    r = client.get(f'/api/v1/projects/{pid}/tasks?page=3&per_page=2', headers=headers)
    body = r.get_json()
    assert len(body['data']) == 1  # dernière page, reste 1 tâche


def test_sort_tasks_by_priority(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, pid, col_id = _make_column(client, headers)
    client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Basse", "priority": "low"}, headers=headers)
    client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Haute", "priority": "high"}, headers=headers)
    client.post(f'/api/v1/columns/{col_id}/tasks', json={"title": "Moyenne", "priority": "medium"}, headers=headers)

    r = client.get(f'/api/v1/projects/{pid}/tasks?sort=priority', headers=headers)
    titles = [t['title'] for t in r.get_json()['data']]
    assert titles == ['Haute', 'Basse', 'Moyenne']  # ordre alphabétique : high, low, medium

    r = client.get(f'/api/v1/projects/{pid}/tasks?sort=-priority', headers=headers)
    titles = [t['title'] for t in r.get_json()['data']]
    assert titles == ['Moyenne', 'Basse', 'Haute']


def test_delete_task(client, auth_headers):
    headers, _ = auth_headers('alice')
    _, _, col_id = _make_column(client, headers)
    tid = client.post(f'/api/v1/columns/{col_id}/tasks',
                       json={"title": "Tâche"}, headers=headers).get_json()['id']

    r = client.delete(f'/api/v1/tasks/{tid}', headers=headers)
    assert r.status_code == 204

    r = client.get(f'/api/v1/tasks/{tid}', headers=headers)
    assert r.status_code == 404