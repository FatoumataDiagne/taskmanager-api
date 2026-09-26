from app.extensions import db
from app.models.task import Task
from app.models.column import Column
from app.errors import APIError
from app.services.workspace_service import get_membership


def _workspace_id_of_column(column):
    """Une colonne appartient à un projet, qui appartient à un workspace."""
    return column.project.workspace_id


def _check_assignee_is_member(workspace_id, assignee_id):
    """Un utilisateur n'est assignable que s'il est membre du workspace (règle métier)."""
    if assignee_id is None:
        return
    if not get_membership(workspace_id, assignee_id):
        raise APIError(
            "L'utilisateur assigné n'est pas membre de ce workspace.",
            status=409, code="NOT_WORKSPACE_MEMBER"
        )


def list_tasks_for_column(column_id):
    return Task.query.filter_by(column_id=column_id).all()


def list_tasks_for_project(project_id, filters):
    """filters : dict optionnel avec column_id, assignee_id, priority, due_date."""
    query = Task.query.join(Column, Task.column_id == Column.id).filter(Column.project_id == project_id)

    if filters.get('column_id') is not None:
        query = query.filter(Task.column_id == filters['column_id'])
    if filters.get('assignee_id') is not None:
        query = query.filter(Task.assignee_id == filters['assignee_id'])
    if filters.get('priority') is not None:
        query = query.filter(Task.priority == filters['priority'])
    if filters.get('due_date') is not None:
        query = query.filter(Task.due_date == filters['due_date'])

    return query.all()


def create_task(column_id, data):
    column = get_column_or_404_local(column_id)
    workspace_id = _workspace_id_of_column(column)
    _check_assignee_is_member(workspace_id, data.get('assignee_id'))

    task = Task(
        title=data['title'],
        description=data.get('description'),
        column_id=column_id,
        assignee_id=data.get('assignee_id'),
        due_date=data.get('due_date'),
        priority=data.get('priority', 'medium'),
    )
    db.session.add(task)
    db.session.commit()
    return task


def get_column_or_404_local(column_id):
    column = Column.query.get(column_id)
    if not column:
        raise APIError("Colonne introuvable.", status=404, code="NOT_FOUND")
    return column


def get_task_or_404(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise APIError("Tâche introuvable.", status=404, code="NOT_FOUND")
    return task


def update_task(task, data):
    current_column = get_column_or_404_local(task.column_id)
    workspace_id = _workspace_id_of_column(current_column)

    if 'column_id' in data:
        new_column = get_column_or_404_local(data['column_id'])
        if new_column.project_id != current_column.project_id:
            raise APIError(
                "Impossible de déplacer une tâche vers une colonne d'un autre projet.",
                status=409, code="INVALID_COLUMN_TARGET"
            )
        task.column_id = data['column_id']

    if 'assignee_id' in data:
        _check_assignee_is_member(workspace_id, data['assignee_id'])
        task.assignee_id = data['assignee_id']

    for field in ('title', 'description', 'due_date', 'priority'):
        if field in data:
            setattr(task, field, data[field])

    db.session.commit()
    return task


def delete_task(task):
    db.session.delete(task)
    db.session.commit()