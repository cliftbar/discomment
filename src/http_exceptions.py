from werkzeug.exceptions import HTTPException


class ModerationApplied(HTTPException):
    code = 420
    description = 'Content moderation applied'
