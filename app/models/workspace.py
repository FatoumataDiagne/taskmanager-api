from datetime import datetime, timezone
from app.extensions import db


class Workspace(db.Model):
    __tablename__ = 'workspaces'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    members = db.relationship(
        'WorkspaceMember', backref='workspace',
        cascade='all, delete-orphan', lazy='select'
    )
    projects = db.relationship(
        'Project', backref='workspace',
        cascade='all, delete-orphan', lazy='select'
    )

    def __repr__(self):
        return f'<Workspace {self.name}>'


class WorkspaceMember(db.Model):
    __tablename__ = 'workspace_members'
    __table_args__ = (
        db.UniqueConstraint('workspace_id', 'user_id', name='uq_workspace_user'),
    )

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'owner' ou 'member'

    user = db.relationship('User', lazy='select')

    def __repr__(self):
        return f'<WorkspaceMember workspace={self.workspace_id} user={self.user_id} role={self.role}>'
