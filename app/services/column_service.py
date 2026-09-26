from app.extensions import db
from app.models.column import Column
from app.errors import APIError


def list_columns_for_project(project_id):
    return Column.query.filter_by(project_id=project_id).order_by(Column.order).all()


def create_column(project_id, name, order=0):
    column = Column(name=name, order=order, project_id=project_id)
    db.session.add(column)
    db.session.commit()
    return column


def get_column_or_404(column_id):
    column = Column.query.get(column_id)
    if not column:
        raise APIError("Colonne introuvable.", status=404, code="NOT_FOUND")
    return column


def update_column(column, data):
    if 'name' in data:
        column.name = data['name']
    if 'order' in data:
        column.order = data['order']
    db.session.commit()
    return column


def delete_column(column):
    db.session.delete(column)
    db.session.commit()