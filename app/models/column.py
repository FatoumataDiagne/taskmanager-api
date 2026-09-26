from app.extensions import db


class Column(db.Model):
    __tablename__ = 'columns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    tasks = db.relationship(
        'Task', backref='column',
        cascade='all, delete-orphan', lazy='select'
    )

    def __repr__(self):
        return f'<Column {self.name}>'
