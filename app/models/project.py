from app.extensions import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active' ou 'archived'

    columns = db.relationship(
        'Column', backref='project',
        cascade='all, delete-orphan', lazy='select',
        order_by='Column.order'
    )

    def __repr__(self):
        return f'<Project {self.name}>'
