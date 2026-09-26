from marshmallow import Schema, fields, validate


class ColumnSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    order = fields.Int(load_default=0)
    project_id = fields.Int(dump_only=True)


class ColumnUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    order = fields.Int()


column_schema = ColumnSchema()
columns_schema = ColumnSchema(many=True)
column_update_schema = ColumnUpdateSchema()