from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import workspace_service as ws
from app.services import project_service as ps
from app.schemas.project_schema import project_schema, projects_schema, project_update_schema

projects_bp = Blueprint('projects', __name__, url_prefix='/api/v1')


@projects_bp.route('/workspaces/<int:workspace_id>/projects', methods=['GET'])
@jwt_required()
def list_projects(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_member(workspace_id, user_id)
    projects = ps.list_projects_for_workspace(workspace_id)
    return jsonify(projects_schema.dump(projects)), 200


@projects_bp.route('/workspaces/<int:workspace_id>/projects', methods=['POST'])
@jwt_required()
def create_project(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_member(workspace_id, user_id)
    data = project_schema.load(request.get_json() or {})
    project = ps.create_project(workspace_id, data['name'])
    return jsonify(project_schema.dump(project)), 201


@projects_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    user_id = int(get_jwt_identity())
    project = ps.get_project_or_404(project_id)
    ws.require_member(project.workspace_id, user_id)
    return jsonify(project_schema.dump(project)), 200


@projects_bp.route('/projects/<int:project_id>', methods=['PATCH'])
@jwt_required()
def update_project(project_id):
    user_id = int(get_jwt_identity())
    project = ps.get_project_or_404(project_id)
    ws.require_member(project.workspace_id, user_id)
    data = project_update_schema.load(request.get_json() or {})
    project = ps.update_project(project, data)
    return jsonify(project_schema.dump(project)), 200


@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = int(get_jwt_identity())
    project = ps.get_project_or_404(project_id)
    ws.require_member(project.workspace_id, user_id)
    ps.delete_project(project)
    return '', 204