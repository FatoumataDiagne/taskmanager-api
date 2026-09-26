from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services import workspace_service as ws
from app.schemas.workspace_schema import (
    workspace_schema, workspaces_schema, workspace_update_schema,
    member_schema, members_schema
)

workspaces_bp = Blueprint('workspaces', __name__, url_prefix='/api/v1/workspaces')


@workspaces_bp.route('', methods=['GET'])
@jwt_required()
def list_workspaces():
    """
    Liste les workspaces dont l'utilisateur est membre.
    ---
    tags: [Workspaces]
    security: [{Bearer: []}]
    responses:
      200:
        description: Liste des workspaces
      401:
        description: Jeton manquant ou invalide
    """
    user_id = int(get_jwt_identity())
    workspaces = ws.list_workspaces_for_user(user_id)
    return jsonify(workspaces_schema.dump(workspaces)), 200


@workspaces_bp.route('', methods=['POST'])
@jwt_required()
def create_workspace():
    """
    Crée un workspace (le créateur en devient owner).
    ---
    tags: [Workspaces]
    security: [{Bearer: []}]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name]
          properties:
            name: {type: string, example: Mon espace}
    responses:
      201:
        description: Workspace créé
      401:
        description: Jeton manquant ou invalide
    """
    user_id = int(get_jwt_identity())
    data = workspace_schema.load(request.get_json() or {}, partial=('owner_id',))
    workspace = ws.create_workspace(name=data['name'], owner_id=user_id)
    return jsonify(workspace_schema.dump(workspace)), 201


@workspaces_bp.route('/<int:workspace_id>', methods=['GET'])
@jwt_required()
def get_workspace(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_member(workspace_id, user_id)
    workspace = ws.get_workspace_or_404(workspace_id)
    return jsonify(workspace_schema.dump(workspace)), 200


@workspaces_bp.route('/<int:workspace_id>', methods=['PATCH'])
@jwt_required()
def update_workspace(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_owner(workspace_id, user_id)
    workspace = ws.get_workspace_or_404(workspace_id)
    data = workspace_update_schema.load(request.get_json() or {})
    workspace = ws.update_workspace(workspace, data)
    return jsonify(workspace_schema.dump(workspace)), 200


@workspaces_bp.route('/<int:workspace_id>', methods=['DELETE'])
@jwt_required()
def delete_workspace(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_owner(workspace_id, user_id)
    workspace = ws.get_workspace_or_404(workspace_id)
    ws.delete_workspace(workspace)
    return '', 204


@workspaces_bp.route('/<int:workspace_id>/members', methods=['GET'])
@jwt_required()
def list_members(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_member(workspace_id, user_id)
    members = ws.list_members(workspace_id)
    return jsonify(members_schema.dump(members)), 200


@workspaces_bp.route('/<int:workspace_id>/members', methods=['POST'])
@jwt_required()
def add_member(workspace_id):
    user_id = int(get_jwt_identity())
    ws.require_owner(workspace_id, user_id)
    data = member_schema.load(request.get_json() or {})
    membership = ws.add_member(workspace_id, data['user_id'], data.get('role', 'member'))
    return jsonify(member_schema.dump(membership)), 201


@workspaces_bp.route('/<int:workspace_id>/members/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(workspace_id, target_user_id):
    user_id = int(get_jwt_identity())
    ws.require_owner(workspace_id, user_id)
    ws.remove_member(workspace_id, target_user_id)
    return '', 204