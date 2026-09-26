from flask import jsonify
from marshmallow import ValidationError


class APIError(Exception):
    """Erreur métier volontaire, avec code HTTP et code applicatif."""

    def __init__(self, message, status=400, code="BAD_REQUEST"):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


def _error_response(code, message, status):
    return jsonify({"error": {"code": code, "message": message, "status": status}}), status


def register_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(err):
        return _error_response(err.code, err.message, err.status)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return _error_response("VALIDATION_ERROR", err.messages, 422)

    @app.errorhandler(404)
    def handle_404(err):
        return _error_response("NOT_FOUND", "Ressource introuvable.", 404)

    @app.errorhandler(405)
    def handle_405(err):
        return _error_response("METHOD_NOT_ALLOWED", "Méthode non autorisée.", 405)

    @app.errorhandler(500)
    def handle_500(err):
        return _error_response("INTERNAL_ERROR", "Erreur interne du serveur.", 500)
