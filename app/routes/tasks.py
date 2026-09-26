from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import workspace_service as ws
from app.services import project_service as ps
from app.services import column_service as cs
from app.services import task_service as ts
from app.schemas.task_schema import task_schema, tasks_schema, task_update_schema

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/v1')


def _require_column_access(column_id, user_id):
    column = cs.get_column_or_404(column_id)
    project = ps.get_project_or_404(column.project_id)
    ws.require_member(project.workspace_id, user_id)
    return column


def _require_task_access(task_id, user_id):
    task = ts.get_task_or_404(task_id)
    _require_column_access(task.column_id, user_id)
    return task


@tasks_bp.route('/columns/<int:column_id>/tasks', methods=['GET'])
@jwt_required()
def list_tasks_in_column(column_id):
    user_id = int(get_jwt_identity())
    _require_column_access(column_id, user_id)
    tasks = ts.list_tasks_for_column(column_id)
    return jsonify(tasks_schema.dump(tasks)), 200


@tasks_bp.route('/columns/<int:column_id>/tasks', methods=['POST'])
@jwt_required()
def create_task(column_id):
    """
    Crée une tâche dans une colonne.
    ---
    tags: [Tasks]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: column_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required: [title]
          properties:
            title: {type: string, example: Rédiger le README}
            description: {type: string}
            assignee_id: {type: integer}
            due_date: {type: string, example: '2026-10-01'}
            priority: {type: string, enum: [low, medium, high]}
    responses:
      201:
        description: Tâche créée
      403:
        description: L'utilisateur n'est pas membre du workspace
      409:
        description: L'assigné n'est pas membre du workspace
    """
    user_id = int(get_jwt_identity())
    _require_column_access(column_id, user_id)
    data = task_schema.load(request.get_json() or {})
    task = ts.create_task(column_id, data)
    return jsonify(task_schema.dump(task)), 201


@tasks_bp.route('/projects/<int:project_id>/tasks', methods=['GET'])
@jwt_required()
def list_tasks_in_project(project_id):
    user_id = int(get_jwt_identity())
    project = ps.get_project_or_404(project_id)
    ws.require_member(project.workspace_id, user_id)

    filters = {
        'column_id': request.args.get('column_id', type=int),
        'assignee_id': request.args.get('assignee_id', type=int),
        'priority': request.args.get('priority'),
        'due_date': request.args.get('due_date'),  # format YYYY-MM-DD
    }
    tasks = ts.list_tasks_for_project(project_id, filters)
    return jsonify(tasks_schema.dump(tasks)), 200


@tasks_bp.route('/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    user_id = int(get_jwt_identity())
    task = _require_task_access(task_id, user_id)
    return jsonify(task_schema.dump(task)), 200


@tasks_bp.route('/tasks/<int:task_id>', methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    """
    Modifie une tâche, y compris son déplacement entre colonnes via column_id.
    ---
    tags: [Tasks]
    security: [{Bearer: []}]
    parameters:
      - in: path
        name: task_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            title: {type: string}
            description: {type: string}
            column_id: {type: integer, description: "déplace la tâche vers cette colonne"}
            assignee_id: {type: integer}
            due_date: {type: string}
            priority: {type: string, enum: [low, medium, high]}
    responses:
      200:
        description: Tâche mise à jour
      409:
        description: Colonne cible d'un autre projet, ou assigné non membre
    """
    user_id = int(get_jwt_identity())
    task = _require_task_access(task_id, user_id)
    data = task_update_schema.load(request.get_json() or {})
    task = ts.update_task(task, data)
    return jsonify(task_schema.dump(task)), 200


@tasks_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())
    task = _require_task_access(task_id, user_id)
    ts.delete_task(task)
    return '', 204