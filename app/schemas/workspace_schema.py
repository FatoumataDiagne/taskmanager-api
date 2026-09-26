from marshmallow import Schema, fields, validate


class WorkspaceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    owner_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


class WorkspaceUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=150))


class WorkspaceMemberSchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    role = fields.Str(load_default='member', validate=validate.OneOf(['owner', 'member']))
    username = fields.Str(attribute='user.username', dump_only=True)


workspace_schema = WorkspaceSchema()
workspaces_schema = WorkspaceSchema(many=True)
workspace_update_schema = WorkspaceUpdateSchema()
member_schema = WorkspaceMemberSchema()
members_schema = WorkspaceMemberSchema(many=True)
