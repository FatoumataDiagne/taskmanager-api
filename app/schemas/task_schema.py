from marshmallow import Schema, fields, validate


class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=False, allow_none=True)
    column_id = fields.Int(dump_only=True)
    assignee_id = fields.Int(required=False, allow_none=True)
    due_date = fields.Date(required=False, allow_none=True)
    priority = fields.Str(load_default='medium', validate=validate.OneOf(['low', 'medium', 'high']))


class TaskUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True)
    column_id = fields.Int()  # déplacement entre colonnes
    assignee_id = fields.Int(allow_none=True)
    due_date = fields.Date(allow_none=True)
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high']))


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)
task_update_schema = TaskUpdateSchema()