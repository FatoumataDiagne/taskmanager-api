from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import workspace_service as ws
from app.services import project_service as ps
from app.services import column_service as cs
from app.schemas.column_schema import column_schema, columns_schema, column_update_schema

columns_bp = Blueprint('columns', __name__, url_prefix='/api/v1')


def _require_project_access(project_id, user_id):
    """Charge le projet et vérifie que l'utilisateur est membre de son workspace."""
    project = ps.get_project_or_404(project_id)
    ws.require_member(project.workspace_id, user_id)
    return project


@columns_bp.route('/projects/<int:project_id>/columns', methods=['GET'])
@jwt_required()
def list_columns(project_id):
    user_id = int(get_jwt_identity())
    _require_project_access(project_id, user_id)
    columns = cs.list_columns_for_project(project_id)
    return jsonify(columns_schema.dump(columns)), 200


@columns_bp.route('/projects/<int:project_id>/columns', methods=['POST'])
@jwt_required()
def create_column(project_id):
    user_id = int(get_jwt_identity())
    _require_project_access(project_id, user_id)
    data = column_schema.load(request.get_json() or {})
    column = cs.create_column(project_id, data['name'], data.get('order', 0))
    return jsonify(column_schema.dump(column)), 201


@columns_bp.route('/columns/<int:column_id>', methods=['PATCH'])
@jwt_required()
def update_column(column_id):
    user_id = int(get_jwt_identity())
    column = cs.get_column_or_404(column_id)
    _require_project_access(column.project_id, user_id)
    data = column_update_schema.load(request.get_json() or {})
    column = cs.update_column(column, data)
    return jsonify(column_schema.dump(column)), 200


@columns_bp.route('/columns/<int:column_id>', methods=['DELETE'])
@jwt_required()
def delete_column(column_id):
    user_id = int(get_jwt_identity())
    column = cs.get_column_or_404(column_id)
    _require_project_access(column.project_id, user_id)
    cs.delete_column(column)
    return '', 204