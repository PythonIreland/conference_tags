from marshmallow import Schema, fields, EXCLUDE, post_load
from attendees import Attendee


class TicketSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    first_name = fields.String(missing=None)
    last_name = fields.String(missing=None)
    name = fields.String(missing=None)
    email = fields.String(missing=None)
    responses = fields.Dict(missing={})
    reference = fields.String(required=True)
    ticket_title = fields.String(attribute="release_title")

    updated_at = fields.DateTime(missing=None)

    @post_load
    def make_oject(self, data, **kwargs):
        return Attendee(data)


class PaginationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    next_page = fields.Integer(missing=None)


class TicketAPISchema(Schema):
    class Meta:
        unknown = EXCLUDE

    tickets = fields.List(fields.Nested(TicketSchema))
    meta = fields.Nested(PaginationSchema())
