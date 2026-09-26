from marshmallow import Schema, fields, validate


class ProjectSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    workspace_id = fields.Int(dump_only=True)
    status = fields.Str(dump_only=True)


class ProjectUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=150))
    status = fields.Str(validate=validate.OneOf(['active', 'archived']))


project_schema = ProjectSchema()
projects_schema = ProjectSchema(many=True)
project_update_schema = ProjectUpdateSchema()