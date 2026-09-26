import logging
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flasgger import Swagger

from app import config
from app.extensions import db, migrate, jwt, cors, limiter
from app.errors import register_error_handlers

load_dotenv()


def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config.config_by_name[config_name])

    jwt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    limiter.init_app(app)

    if app.config.get('DEBUG'):
        Swagger(app, template={
            "swagger": "2.0",
            "info": {
                "title": "TaskManager API",
                "description": "API REST de gestion de tâches (workspaces, projets, colonnes, tâches).",
                "version": "1.0.0"
            },
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Jeton JWT au format : Bearer <token>"
                }
            }
        }, config={
            "headers": [],
            "specs": [{"endpoint": "apispec", "route": "/apispec.json"}],
            "static_url_path": "/flasgger_static",
            "specs_route": "/docs/"
        })

    register_error_handlers(app)
    _register_jwt_error_handlers(jwt)
    _register_security_headers(app)
    _configure_logging(app)

    # Modèles importés pour qu'Alembic les détecte
    from app.models import user, workspace, project, column, task  # noqa: F401

    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.workspaces import workspaces_bp
    from app.routes.projects import projects_bp
    from app.routes.columns import columns_bp
    from app.routes.tasks import tasks_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(columns_bp)
    app.register_blueprint(tasks_bp)

    return app


def _register_jwt_error_handlers(jwt_manager):
    def _err(code, message, status):
        return jsonify({"error": {"code": code, "message": message, "status": status}}), status

    @jwt_manager.unauthorized_loader
    def missing_token(reason):
        return _err("UNAUTHORIZED", "Jeton d'authentification manquant.", 401)

    @jwt_manager.invalid_token_loader
    def invalid_token(reason):
        return _err("UNAUTHORIZED", "Jeton d'authentification invalide.", 401)

    @jwt_manager.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return _err("UNAUTHORIZED", "Jeton d'authentification expiré.", 401)


def _register_security_headers(app):
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        return response


def _configure_logging(app):
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(message)s'
        ))
        app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    @app.after_request
    def log_request(response):
        app.logger.info(
            '%s %s -> %s', request.method, request.path, response.status_code
        )
        return response