from app.extensions import db
from app.models.workspace import Workspace, WorkspaceMember
from app.models.user import User
from app.errors import APIError


def list_workspaces_for_user(user_id):
    """Workspaces où l'utilisateur est membre (quel que soit son rôle)."""
    return (
        Workspace.query
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user_id)
        .all()
    )


def create_workspace(name, owner_id):
    """Crée un workspace et son créateur comme membre 'owner'."""
    workspace = Workspace(name=name, owner_id=owner_id)
    db.session.add(workspace)
    db.session.flush()  # pour obtenir workspace.id avant le commit

    membership = WorkspaceMember(workspace_id=workspace.id, user_id=owner_id, role='owner')
    db.session.add(membership)
    db.session.commit()
    return workspace


def get_membership(workspace_id, user_id):
    """Retourne l'appartenance (avec rôle) de l'utilisateur au workspace, ou None."""
    return WorkspaceMember.query.filter_by(workspace_id=workspace_id, user_id=user_id).first()


def get_workspace_or_404(workspace_id):
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        raise APIError("Workspace introuvable.", status=404, code="NOT_FOUND")
    return workspace


def require_member(workspace_id, user_id):
    """Lève 403 si l'utilisateur n'est pas membre du workspace. Retourne l'appartenance sinon."""
    membership = get_membership(workspace_id, user_id)
    if not membership:
        raise APIError("Vous n'êtes pas membre de ce workspace.", status=403, code="FORBIDDEN")
    return membership


def require_owner(workspace_id, user_id):
    """Lève 403 si l'utilisateur n'est pas owner du workspace. Retourne l'appartenance sinon."""
    membership = require_member(workspace_id, user_id)
    if membership.role != 'owner':
        raise APIError("Seul le owner du workspace peut effectuer cette action.", status=403, code="FORBIDDEN")
    return membership


def update_workspace(workspace, data):
    if 'name' in data:
        workspace.name = data['name']
    db.session.commit()
    return workspace


def delete_workspace(workspace):
    db.session.delete(workspace)
    db.session.commit()


def list_members(workspace_id):
    return WorkspaceMember.query.filter_by(workspace_id=workspace_id).all()


def add_member(workspace_id, user_id, role='member'):
    if not User.query.get(user_id):
        raise APIError("Utilisateur introuvable.", status=404, code="NOT_FOUND")
    if get_membership(workspace_id, user_id):
        raise APIError("Cet utilisateur est déjà membre du workspace.", status=409, code="ALREADY_MEMBER")

    membership = WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=role)
    db.session.add(membership)
    db.session.commit()
    return membership


def remove_member(workspace_id, user_id):
    membership = get_membership(workspace_id, user_id)
    if not membership:
        raise APIError("Cet utilisateur n'est pas membre du workspace.", status=404, code="NOT_FOUND")
    if membership.role == 'owner':
        raise APIError("Le owner du workspace ne peut pas être retiré.", status=409, code="CANNOT_REMOVE_OWNER")

    db.session.delete(membership)
    db.session.commit()
