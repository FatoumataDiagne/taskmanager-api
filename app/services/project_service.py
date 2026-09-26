from app.extensions import db
from app.models.project import Project
from app.errors import APIError


def list_projects_for_workspace(workspace_id):
    return Project.query.filter_by(workspace_id=workspace_id).all()


def create_project(workspace_id, name):
    project = Project(name=name, workspace_id=workspace_id)
    db.session.add(project)
    db.session.commit()
    return project


def get_project_or_404(project_id):
    project = Project.query.get(project_id)
    if not project:
        raise APIError("Projet introuvable.", status=404, code="NOT_FOUND")
    return project


def update_project(project, data):
    if 'name' in data:
        project.name = data['name']
    if 'status' in data:
        project.status = data['status']
    db.session.commit()
    return project


def delete_project(project):
    db.session.delete(project)
    db.session.commit()